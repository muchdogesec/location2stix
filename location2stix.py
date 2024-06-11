import csv
import uuid
import json
import hashlib
import requests
import shutil
import os
from stix2 import FileSystemSource, FileSystemSink, Location, Bundle, Relationship, parse

# Constants
NAMESPACE_UUID = uuid.UUID("674a16c1-8b43-5c3e-8692-b3d8935e4903")

# URLs for the external STIX objects
IDENTITY_URL = "https://raw.githubusercontent.com/muchdogesec/stix4doge/main/objects/identity/location2stix.json"
MARKING_DEFINITION_URL = "https://raw.githubusercontent.com/muchdogesec/stix4doge/main/objects/marking-definition/location2stix.json"

# Helper functions
def generate_uuid_v5(name):
    return str(uuid.uuid5(NAMESPACE_UUID, name))

def generate_relationship_uuid_v5(source_ref, target_ref):
    value = source_ref + "+" + target_ref
    return str(uuid.uuid5(NAMESPACE_UUID, value))

def convert_subregion(subregion):
    return subregion.lower().replace(" ", "-").replace(" and", "")

def read_csv(file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        data = [row for row in reader]
    return data

def create_location_object(name, region, alpha2, alpha3, iso_3166_2, country_code):
    return Location(
        id="location--" + generate_uuid_v5(name),
        created_by_ref=IDENTITY_ID,
        created="2020-01-01T00:00:00.000Z",
        modified="2020-01-01T00:00:00.000Z",
        name=name,
        region=convert_subregion(region),
        country=alpha2,
        object_marking_refs=[MARKING_DEFINITION_ID, "marking-definition--94868c89-83c2-464b-929b-a1a8aa3c8487"],
        external_references=[
            {"source_name": "alpha-3", "external_id": alpha3},
            {"source_name": "iso_3166-2", "external_id": iso_3166_2},
            {"source_name": "country-code", "external_id": country_code},
        ]
    )

def create_intermediate_region_object(name, intermediate_region_code):
    return Location(
        id="location--" + generate_uuid_v5(name),
        created_by_ref=IDENTITY_ID,
        created="2020-01-01T00:00:00.000Z",
        modified="2020-01-01T00:00:00.000Z",
        name=name,
        region=convert_subregion(name),
        object_marking_refs=[MARKING_DEFINITION_ID, "marking-definition--94868c89-83c2-464b-929b-a1a8aa3c8487"],
        external_references=[
            {"source_name": "intermediate-region-code", "external_id": intermediate_region_code}
        ]
    )

def create_subregion_object(name, sub_region_code):
    return Location(
        id="location--" + generate_uuid_v5(name),
        created_by_ref=IDENTITY_ID,
        created="2020-01-01T00:00:00.000Z",
        modified="2020-01-01T00:00:00.000Z",
        name=name,
        region=convert_subregion(name),
        object_marking_refs=[MARKING_DEFINITION_ID, "marking-definition--94868c89-83c2-464b-929b-a1a8aa3c8487"],
        external_references=[
            {"source_name": "sub-region-code", "external_id": sub_region_code}
        ]
    )

def create_region_object(name, region_code):
    return Location(
        id="location--" + generate_uuid_v5(name),
        created_by_ref=IDENTITY_ID,
        created="2020-01-01T00:00:00.000Z",
        modified="2020-01-01T00:00:00.000Z",
        name=name,
        region=convert_subregion(name),
        object_marking_refs=[MARKING_DEFINITION_ID, "marking-definition--94868c89-83c2-464b-929b-a1a8aa3c8487"],
        external_references=[
            {"source_name": "region-code", "external_id": region_code}
        ]
    )

def create_relationship(source_ref, target_ref, relationship_type):
    return Relationship(
        id="relationship--" + generate_relationship_uuid_v5(source_ref, target_ref),
        created_by_ref=IDENTITY_ID,
        created="2020-01-01T00:00:00.000Z",
        modified="2020-01-01T00:00:00.000Z",
        relationship_type=relationship_type,
        source_ref=source_ref,
        target_ref=target_ref,
        object_marking_refs=[MARKING_DEFINITION_ID, "marking-definition--94868c89-83c2-464b-929b-a1a8aa3c8487"]
    )

def fetch_stix_object(url):
    response = requests.get(url)
    response.raise_for_status()
    return parse(response.json())

def main():
    csv_file_path = 'input_data/ISO-3166-Countries-with-Regional-Codes.csv'
    data = read_csv(csv_file_path)

    identity_obj = fetch_stix_object(IDENTITY_URL)
    marking_definition_obj = fetch_stix_object(MARKING_DEFINITION_URL)

    global IDENTITY_ID, MARKING_DEFINITION_ID
    IDENTITY_ID = identity_obj["id"]
    MARKING_DEFINITION_ID = marking_definition_obj["id"]

    # Setting up the filestore
    filestore_path = "stix2_objects"
    if os.path.exists(filestore_path):
        shutil.rmtree(filestore_path)
    os.makedirs(filestore_path)
    
    sink = FileSystemSink(filestore_path)
    src = FileSystemSource(filestore_path)
    sink.add(identity_obj)
    sink.add(marking_definition_obj)

    regions = {}
    subregions = {}
    intermediate_regions = {}
    countries = []

    for row in data:
        country_name = row['name']
        region_name = row['region']
        sub_region_name = row['sub-region']
        intermediate_region_name = row.get('intermediate-region', '')
        alpha2 = row['alpha-2']
        alpha3 = row['alpha-3']
        iso_3166_2 = row['iso_3166-2']
        country_code = row['country-code']

        if not country_name:
            continue

        country = create_location_object(country_name, sub_region_name, alpha2, alpha3, iso_3166_2, country_code)
        countries.append(country)
        if not src.get(country.id):
            sink.add(country)
            print(f"Created country {country_name}")

        if region_name and region_name not in regions:
            region = create_region_object(region_name, region_name)
            regions[region_name] = region
            if not src.get(region.id):
                sink.add(region)
                print(f"Created region {region_name}")

        if sub_region_name and sub_region_name not in subregions:
            subregion = create_subregion_object(sub_region_name, sub_region_name)
            subregions[sub_region_name] = subregion
            if not src.get(subregion.id):
                sink.add(subregion)
                print(f"Created sub-region {sub_region_name}")

        if intermediate_region_name and intermediate_region_name not in intermediate_regions:
            intermediate_region = create_intermediate_region_object(intermediate_region_name, intermediate_region_name)
            intermediate_regions[intermediate_region_name] = intermediate_region
            if not src.get(intermediate_region.id):
                sink.add(intermediate_region)
                print(f"Created intermediate-region {intermediate_region_name}")

    relationships = []
    for country in countries:
        country_id = country.id
        sub_region_name = next((row['sub-region'] for row in data if row['name'] == country.name), '')
        intermediate_region_name = next((row.get('intermediate-region', '') for row in data if row['name'] == country.name), '')
        region_name = next((row['region'] for row in data if row['name'] == country.name), '')

        if sub_region_name and sub_region_name in subregions:
            relationship = create_relationship(country_id, subregions[sub_region_name].id, 'sub-region')
            relationships.append(relationship)
            if not src.get(relationship.id):
                sink.add(relationship)
            print(f"Created relationship between country {country.name} and sub-region {sub_region_name}")

        if region_name and region_name in regions:
            relationship = create_relationship(country_id, regions[region_name].id, 'region')
            relationships.append(relationship)
            if not src.get(relationship.id):
                sink.add(relationship)
            print(f"Created relationship between country {country.name} and region {region_name}")

        if intermediate_region_name and intermediate_region_name in intermediate_regions:
            relationship = create_relationship(country_id, intermediate_regions[intermediate_region_name].id, 'intermediate-region')
            relationships.append(relationship)
            if not src.get(relationship.id):
                sink.add(relationship)
            print(f"Created relationship between country {country.name} and intermediate-region {intermediate_region_name}")

    # Create relationships between sub-regions and regions
    for sub_region_name, subregion in subregions.items():
        region_name = next((row['region'] for row in data if row['sub-region'] == sub_region_name), '')
        if region_name and region_name in regions:
            relationship = create_relationship(subregion.id, regions[region_name].id, 'region')
            relationships.append(relationship)
            if not src.get(relationship.id):
                sink.add(relationship)
            print(f"Created relationship between sub-region {sub_region_name} and region {region_name}")

    # Create relationships between intermediate-regions and sub-regions
    for intermediate_region_name, intermediate_region in intermediate_regions.items():
        sub_region_name = next((row['sub-region'] for row in data if row.get('intermediate-region', '') == intermediate_region_name), '')
        if sub_region_name and sub_region_name in subregions:
            relationship = create_relationship(intermediate_region.id, subregions[sub_region_name].id, 'sub-region')
            relationships.append(relationship)
            if not src.get(relationship.id):
                sink.add(relationship)
            print(f"Created relationship between intermediate-region {intermediate_region_name} and sub-region {sub_region_name}")

    all_objects = list(src.query()) + relationships  # Query all objects in the filestore and add relationships
    bundle = Bundle(objects=all_objects, allow_custom=True)
    bundle_dict = json.loads(bundle.serialize())  # Convert to dictionary to allow pretty-printing

    with open('stix2_objects/locations-bundle.json', 'w') as f:
        json.dump(bundle_dict, f, indent=4)

if __name__ == '__main__':
    main()
