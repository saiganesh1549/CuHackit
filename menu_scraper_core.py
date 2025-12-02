import requests
import csv
from datetime import date
import os

def fetch_menu(location="the-dish-at-mcalister", out_file="clemson_menu_core_today.csv"):
    query_date = date.today().isoformat()

    url = "https://api.elevate-dxp.com/api/mesh/c087f756-cc72-4649-a36f-3a41b700c519/graphql"

    payload = {
        "operationName": "getLocationRecipes",
        "variables": {
            "campusUrlKey": "campus",
            "locationUrlKey": location,
            "date": query_date,
            "mealPeriod": 25,
            "viewType": "DAILY",
            "dayPart": [],
            "menuTypes": []
        },
        "query": """
        query getLocationRecipes(
            $campusUrlKey: String!,
            $locationUrlKey: String!,
            $date: String!,
            $mealPeriod: Int,
            $viewType: Commerce_MenuViewType!,
            $dayPart: [String],
            $menuTypes: [String]
        ) {
            getLocationRecipes(
                campusUrlKey: $campusUrlKey,
                locationUrlKey: $locationUrlKey,
                date: $date,
                mealPeriod: $mealPeriod,
                viewType: $viewType,
                dayPart: $dayPart,
                menuTypes: $menuTypes
            ) {
                locationRecipesMap {
                    dateSkuMap {
                        date
                        stations {
                            id
                            skus {
                                simple
                            }
                        }
                    }
                }
                products {
                    items {
                        productView {
                            sku
                            attributes {
                                name
                                value
                            }
                        }
                    }
                }
            }
        }
        """
    }

    headers = {
        "Content-Type": "application/json",
        "Origin": "https://clemson.mydininghub.com",
        "Referer": "https://clemson.mydininghub.com/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3)",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "x-tenant-key": "clemson",
        "apollographql-client-name": "mydininghub-web",
        "apollographql-client-version": "1.0.0"
    }

    resp = requests.post(url, json=payload, headers=headers)

    print("STATUS:", resp.status_code)

    if resp.status_code != 200:
        print("Raw response (first 400 chars):")
        print(resp.text[:400])
        return

    json_data = resp.json()["data"]["getLocationRecipes"]

    # Build SKU → attributes map
    sku_info = {}
    for item in json_data["products"]["items"]:
        sku = item["productView"]["sku"]
        attrs = {a["name"]: a["value"] for a in item["productView"]["attributes"]}
        sku_info[sku] = attrs

    # Get dateSkuMap
    date_map = json_data["locationRecipesMap"]["dateSkuMap"]
    if not date_map:
        print("No menu data available today.")
        return

    stations = date_map[0]["stations"]

    menu = []
    for station in stations:
        for sku in station["skus"]["simple"]:
            attrs = sku_info.get(sku, {})
            menu.append({
                "station": station["id"],
                "sku": sku,
                "item_name": attrs.get("marketing_name"),
                "calories": attrs.get("calories"),
                "protein": attrs.get("protein"),
                "fat": attrs.get("total_fat"),
                "carbs": attrs.get("total_carbohydrates"),
                "allergens": attrs.get("allergen_statement"),
                "serving_size": attrs.get("serving_size"),
                "serving_unit": attrs.get("serving_unit"),
                "date": query_date
            })

    if not menu:
        print("Menu is empty for this hall today.")
        return

    with open(out_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=menu[0].keys())
        writer.writeheader()
        writer.writerows(menu)

    print(f"Saved {len(menu)} items → {os.path.abspath(out_file)}")

fetch_menu()