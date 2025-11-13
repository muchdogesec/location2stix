import csv
import uuid
import json
import hashlib
import requests
import shutil
import os
from stix2 import (
    FileSystemSource,
    FileSystemSink,
    Location,
    Bundle,
    Relationship,
    parse,
)

# Constants
NAMESPACE_UUID = uuid.UUID("674a16c1-8b43-5c3e-8692-b3d8935e4903")

# URLs for the external STIX objects
IDENTITY_URL = "https://raw.githubusercontent.com/muchdogesec/stix4doge/main/objects/identity/dogesec.json"
MARKING_DEFINITION_URL = "https://raw.githubusercontent.com/muchdogesec/stix4doge/main/objects/marking-definition/location2stix.json"
OPENCTI_EXTENSION_URL = "https://raw.githubusercontent.com/muchdogesec/stix2extensions/refs/heads/main/automodel_generated/extension-definitions/properties/location-opencti.json"


def load_file_from_url(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an HTTPError for bad responses
    return response.json()


IDENTITY_OBJ, MARKING_OBJ, OPENCTI_EXTENSION = [
    load_file_from_url(url) for url in [IDENTITY_URL, MARKING_DEFINITION_URL, OPENCTI_EXTENSION_URL]
]
IDENTITY_ID = IDENTITY_OBJ["id"]
MARKING_REFS = [
    "marking-definition--94868c89-83c2-464b-929b-a1a8aa3c8487",
    MARKING_OBJ["id"],
]


# Helper functions
def generate_location_id(name):
    return "location--" + str(uuid.uuid5(NAMESPACE_UUID, name))


def generate_relationship_uuid_v5(source_ref, target_ref):
    value = source_ref + "+" + target_ref
    return str(uuid.uuid5(NAMESPACE_UUID, value))


def convert_subregion(subregion):
    return (
        subregion.lower().replace(" ", "-").replace("-and-", "-").replace("-the-", "-")
    )


def read_csv(file_path):
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            yield {k.replace("-", "_"): v for k, v in row.items()}


def create_country_object(
    name, region, alpha_2, alpha_3, iso_3166_2, country_code, lng, lat, **kwargs
):
    print(name)
    return Location(
        id=generate_location_id(name),
        created_by_ref=IDENTITY_ID,
        created="2020-01-01T00:00:00.000Z",
        modified="2020-01-01T00:00:00.000Z",
        name=name,
        region=convert_subregion(region),
        latitude=lat and float(lat) or None,
        longitude=lng and float(lng) or None,
        country=alpha_2,
        object_marking_refs=MARKING_REFS,
        external_references=[
            {"source_name": "location2stix", "external_id": alpha_2},
            {"source_name": "type", "external_id": "country"},
            {"source_name": "alpha-2", "external_id": alpha_2},
            {"source_name": "alpha-3", "external_id": alpha_3},
            {"source_name": "iso_3166-2", "external_id": iso_3166_2},
            {"source_name": "country-code", "external_id": country_code},
        ],
        extensions={
            "extension-definition--b9c1f945-80be-519d-9d7f-0cede26032e9": {
                "extension_type": "toplevel-property-extension"
            }
        },
        x_opencti_location_type=["Country"],
        x_opencti_aliases=[
            alpha_3,
            alpha_2,
        ],
    )


def create_region_object(name, region_code):
    return Location(
        id=generate_location_id(name),
        created_by_ref=IDENTITY_ID,
        created="2020-01-01T00:00:00.000Z",
        modified="2020-01-01T00:00:00.000Z",
        name=name,
        region=convert_subregion(name),
        object_marking_refs=MARKING_REFS,
        external_references=[
            {
                "source_name": "location2stix",
                "external_id": convert_subregion(region_code),
            },
            {"source_name": "region-code", "external_id": region_code},
            {"source_name": "type", "external_id": "region"},
        ],
        extensions={
            "extension-definition--b9c1f945-80be-519d-9d7f-0cede26032e9": {
                "extension_type": "toplevel-property-extension"
            }
        },
        x_opencti_location_type=["Region"],
    )


def create_subregion_object(name, sub_region_code):
    return Location(
        id=generate_location_id(name),
        created_by_ref=IDENTITY_ID,
        created="2020-01-01T00:00:00.000Z",
        modified="2020-01-01T00:00:00.000Z",
        name=name,
        region=convert_subregion(name),
        object_marking_refs=MARKING_REFS,
        external_references=[
            {
                "source_name": "location2stix",
                "external_id": convert_subregion(sub_region_code),
            },
            {"source_name": "sub-region-code", "external_id": sub_region_code},
            {"source_name": "type", "external_id": "sub-region"},
        ],
        extensions={
            "extension-definition--b9c1f945-80be-519d-9d7f-0cede26032e9": {
                "extension_type": "toplevel-property-extension"
            }
        },
        x_opencti_location_type=["Region"],
    )


def create_intermediate_region_object(name, intermediate_region_code):
    return Location(
        id=generate_location_id(name),
        created_by_ref=IDENTITY_ID,
        created="2020-01-01T00:00:00.000Z",
        modified="2020-01-01T00:00:00.000Z",
        name=name,
        region=convert_subregion(name),
        object_marking_refs=MARKING_REFS,
        external_references=[
            {
                "source_name": "location2stix",
                "external_id": convert_subregion(intermediate_region_code),
            },
            {
                "source_name": "intermediate-region-code",
                "external_id": intermediate_region_code,
            },
            {"source_name": "type", "external_id": "intermediate-region"},
        ],
        extensions={
            "extension-definition--b9c1f945-80be-519d-9d7f-0cede26032e9": {
                "extension_type": "toplevel-property-extension"
            }
        },
        x_opencti_location_type=["Region"],
    )


def create_relationship(
    source_ref, target_ref, relationship_type, source_name, target_name
):
    return Relationship(
        id="relationship--" + generate_relationship_uuid_v5(source_ref, target_ref),
        created_by_ref=IDENTITY_ID,
        created="2020-01-01T00:00:00.000Z",
        modified="2020-01-01T00:00:00.000Z",
        description=f"{source_name} belongs to the {relationship_type} of {target_name}",
        relationship_type="located-at",
        source_ref=source_ref,
        target_ref=target_ref,
        object_marking_refs=MARKING_REFS,
    )


def fetch_stix_object(url):
    response = requests.get(url)
    response.raise_for_status()
    return parse(response.json())


def generate_md5_from_list(stix_objects):
    md5_hash = hashlib.md5()
    for obj in sorted(stix_objects, key=lambda x: x["id"]):
        md5_hash.update(obj["id"].encode("utf-8"))
    return md5_hash.hexdigest()


def main():
    csv_file_path = "input_data/ISO-3166-Countries-with-Regional-Codes.csv"
    data = list(read_csv(csv_file_path))

    # Setting up the filestore
    filestore_path = "stix2_objects"
    if os.path.exists(filestore_path):
        shutil.rmtree(filestore_path)
    os.makedirs(filestore_path)

    sink = FileSystemSink(filestore_path)
    src = FileSystemSource(filestore_path)
    sink.add(IDENTITY_OBJ)
    sink.add(MARKING_OBJ)
    sink.add(OPENCTI_EXTENSION)

    regions = {}
    subregions = {}
    intermediate_regions = {}
    countries = []
    data_map = {}

    for row in data:
        country_name = row["name"]
        region_name = row["region"]
        sub_region_name = row["sub_region"]
        intermediate_region_name = row.get("intermediate_region", "")
        data_map[country_name] = row
        data_map[intermediate_region_name] = row
        data_map[sub_region_name] = row

        if not country_name:
            continue

        country = create_country_object(**row)
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

        if (
            intermediate_region_name
            and intermediate_region_name not in intermediate_regions
        ):
            intermediate_region = create_intermediate_region_object(
                intermediate_region_name, intermediate_region_name
            )
            intermediate_regions[intermediate_region_name] = intermediate_region
            if not src.get(intermediate_region.id):
                sink.add(intermediate_region)
                print(f"Created intermediate-region {intermediate_region_name}")

    relationships = []
    for country in countries:
        country_id = country.id
        sub_region_name = data_map[country.name].get("sub_region")
        intermediate_region_name = data_map[country.name].get("intermediate_region")
        region_name = data_map[country.name].get("region")

        if sub_region_name and sub_region_name in subregions:
            relationship = create_relationship(
                source_ref=country_id,
                target_ref=subregions[sub_region_name].id,
                relationship_type="sub-region",
                source_name=country.name,
                target_name=subregions[sub_region_name].name,
            )
            relationships.append(relationship)
            if not src.get(relationship.id):
                sink.add(relationship)
            print(
                f"Created relationship between country {country.name} and sub-region {sub_region_name}"
            )

        if region_name and region_name in regions:
            relationship = create_relationship(
                source_ref=country_id,
                target_ref=regions[region_name].id,
                relationship_type="region",
                source_name=country.name,
                target_name=regions[region_name].name,
            )
            relationships.append(relationship)
            if not src.get(relationship.id):
                sink.add(relationship)
            print(
                f"Created relationship between country {country.name} and region {region_name}"
            )

        if (
            intermediate_region_name
            and intermediate_region_name in intermediate_regions
        ):
            relationship = create_relationship(
                source_ref=country_id,
                target_ref=intermediate_regions[intermediate_region_name].id,
                relationship_type="intermediate-region",
                source_name=country.name,
                target_name=intermediate_regions[intermediate_region_name].name,
            )
            relationships.append(relationship)
            if not src.get(relationship.id):
                sink.add(relationship)
            print(
                f"Created relationship between country {country.name} and intermediate-region {intermediate_region_name}"
            )

    # Create relationships between sub-regions and regions
    for sub_region_name, subregion in subregions.items():
        region_name = data_map[sub_region_name].get("region")
        if region_name and region_name in regions:
            relationship = create_relationship(
                source_ref=subregion.id,
                target_ref=regions[region_name].id,
                relationship_type="region",
                source_name=subregion.name,
                target_name=regions[region_name].name,
            )
            relationships.append(relationship)
            if not src.get(relationship.id):
                sink.add(relationship)
            print(
                f"Created relationship between sub-region {sub_region_name} and region {region_name}"
            )

    # Create relationships between intermediate-regions and sub-regions
    for intermediate_region_name, intermediate_region in intermediate_regions.items():
        sub_region_name = data_map[intermediate_region_name].get("sub_region")
        if sub_region_name and sub_region_name in subregions:
            relationship = create_relationship(
                source_ref=intermediate_region.id,
                target_ref=subregions[sub_region_name].id,
                relationship_type="sub-region",
                source_name=intermediate_region.name,
                target_name=subregions[sub_region_name].name,
            )
            relationships.append(relationship)
            if not src.get(relationship.id):
                sink.add(relationship)
            print(
                f"Created relationship between intermediate-region {intermediate_region_name} and sub-region {sub_region_name}"
            )

    all_objects = (
        list(src.query()) + relationships
    )  # Query all objects in the filestore and add relationships

    # Serialize objects before generating UUID
    serialized_objects = [json.loads(obj.serialize()) for obj in all_objects]
    bundle_uuid = "bundle--" + str(
        uuid.uuid5(NAMESPACE_UUID, generate_md5_from_list(serialized_objects))
    )

    bundle = {"type": "bundle", "id": bundle_uuid, "objects": serialized_objects}

    with open("stix2_objects/locations-bundle.json", "w") as f:
        json.dump(bundle, f, indent=4)


if __name__ == "__main__":
    main()
