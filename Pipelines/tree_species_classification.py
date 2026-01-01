import requests
import API_Key_storage

API_KEY = API_Key_storage.give_api_key()   # put your key here
IMAGE_PATH = r"C:\Users\family_2\Documents\GitHub\VitalArbor\2025-26_Data_Images\11-9-2025\Crabapple_Afternoon_Images\Crabapple_Tree_Trunk.png"

# url = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}"

# files = [
#     ('images', (IMAGE_PATH, open(IMAGE_PATH, 'rb'), 'image/jpeg'))
# ]

# data = {
#     'organs': ['habit']   # just one organ
# }

# response = requests.post(url, files=files, data=data)
# result = response.json()

# print(result)
# best = result['results'][0]
# species = best['species']['scientificName']
# score = best['score']
# best = result['results'][0]
# species = best.get('species')

# # Case 1: species is a dict (full metadata)
# if isinstance(species, dict):
#     # Family
#     family_field = species.get('family')
#     if isinstance(family_field, dict):
#         family = family_field.get('scientificName', 'Unknown')
#     else:
#         family = family_field or "Unknown"

#     # Common names
#     common_names = species.get('commonNames', [])
#     primary_common = common_names[0] if common_names else "Unknown"

# # Case 2: species is a string (only scientific name returned)
# elif isinstance(species, str):
#     family = "Unknown"
#     primary_common = species  # fallback to scientific name

# else:
#     family = "Unknown"
#     primary_common = "Unknown"

# # print("Family:", family)
# # print("Common name:", primary_common)

# clean_name = species.get("scientificNameWithoutAuthor", species.get("scientificName"))
# print(f"Predicted species: {clean_name} (confidence {score:.2f})")
# # print(f"Family: {family}")
# # print(f"Common name: {primary_common}")

def get_species_info(API_KEY, image_path, need_family, need_common_name):
    IMAGE_PATH = image_path

    url = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}"

    files = [
        ('images', (IMAGE_PATH, open(IMAGE_PATH, 'rb'), 'image/jpeg'))
    ]

    data = {
        'organs': ['habit']   # just one organ
    }

    response = requests.post(url, files=files, data=data)
    result = response.json()

    best = result['results'][0]
    species = best['species']['scientificName']
    score = best['score']
    best = result['results'][0]
    species = best.get('species')
    clean_name = species.get("scientificNameWithoutAuthor", species.get("scientificName"))
    if need_family:
        if score > 0.8:
            multiplier = 1
            if isinstance(species, dict):
                # Family
                family_field = species.get('family')
                if isinstance(family_field, dict):
                    family = family_field.get('scientificName', 'Unknown')
                else:
                    family = family_field or "Unknown"

                # Common names
                common_names = species.get('commonNames', [])
                primary_common = common_names[0] if common_names else "Unknown"

            # Case 2: species is a string (only scientific name returned)
            elif isinstance(species, str):
                family = "Unknown"
                primary_common = species  # fallback to scientific name

            else:
                family = "Unknown"
                primary_common = "Unknown"
            return multiplier, clean_name, family, score
        elif score < 0.8 and score > 0.5:
            multiplier = 0.75
            if isinstance(species, dict):
                    # Family
                    family_field = species.get('family')
                    if isinstance(family_field, dict):
                        family = family_field.get('scientificName', 'Unknown')
                    else:
                        family = family_field or "Unknown"

                    # Common names
                    common_names = species.get('commonNames', [])
                    primary_common = common_names[0] if common_names else "Unknown"

            # Case 2: species is a string (only scientific name returned)
            elif isinstance(species, str):
                family = "Unknown"
                primary_common = species  # fallback to scientific name

            else:
                family = "Unknown"
                primary_common = "Unknown"
            return multiplier, clean_name, family, score

        else:
            multiplier = 0.45
            if isinstance(species, dict):
                # Family
                family_field = species.get('family')
                if isinstance(family_field, dict):
                    family = family_field.get('scientificName', 'Unknown')
                else:
                    family = family_field or "Unknown"

                # Common names
                common_names = species.get('commonNames', [])
                primary_common = common_names[0] if common_names else "Unknown"

            # Case 2: species is a string (only scientific name returned)
            elif isinstance(species, str):
                family = "Unknown"
                primary_common = species  # fallback to scientific name

            else:
                family = "Unknown"
                primary_common = "Unknown"
            return multiplier, clean_name, family, score
    elif need_common_name:
        if score > 0.8:
            multiplier = 1
            if isinstance(species, dict):
                # Family
                family_field = species.get('family')
                if isinstance(family_field, dict):
                    family = family_field.get('scientificName', 'Unknown')
                else:
                    family = family_field or "Unknown"

                # Common names
                common_names = species.get('commonNames', [])
                primary_common = common_names[0] if common_names else "Unknown"

            # Case 2: species is a string (only scientific name returned)
            elif isinstance(species, str):
                family = "Unknown"
                primary_common = species  # fallback to scientific name

            else:
                family = "Unknown"
                primary_common = "Unknown"
            return multiplier, clean_name, primary_common, score
        elif score < 0.8 and score > 0.5:
            multiplier = 0.75
            if isinstance(species, dict):
                # Family
                family_field = species.get('family')
                if isinstance(family_field, dict):
                    family = family_field.get('scientificName', 'Unknown')
                else:
                    family = family_field or "Unknown"

                # Common names
                common_names = species.get('commonNames', [])
                primary_common = common_names[0] if common_names else "Unknown"

            # Case 2: species is a string (only scientific name returned)
            elif isinstance(species, str):
                family = "Unknown"
                primary_common = species  # fallback to scientific name

            else:
                family = "Unknown"
                primary_common = "Unknown"
            return multiplier, clean_name, primary_common
        else:
            multiplier = 0.45
            if isinstance(species, dict):
                # Family
                family_field = species.get('family')
                if isinstance(family_field, dict):
                    family = family_field.get('scientificName', 'Unknown')
                else:
                    family = family_field or "Unknown"

                # Common names
                common_names = species.get('commonNames', [])
                primary_common = common_names[0] if common_names else "Unknown"

            # Case 2: species is a string (only scientific name returned)
            elif isinstance(species, str):
                family = "Unknown"
                primary_common = species  # fallback to scientific name

            else:
                family = "Unknown"
                primary_common = "Unknown"
            return multiplier, clean_name, primary_common
    elif need_family and need_common_name:
        if score > 0.8:
            multiplier = 1
            if isinstance(species, dict):
                # Family
                family_field = species.get('family')
                if isinstance(family_field, dict):
                    family = family_field.get('scientificName', 'Unknown')
                else:
                    family = family_field or "Unknown"

                # Common names
                common_names = species.get('commonNames', [])
                primary_common = common_names[0] if common_names else "Unknown"

            # Case 2: species is a string (only scientific name returned)
            elif isinstance(species, str):
                family = "Unknown"
                primary_common = species  # fallback to scientific name

            else:
                family = "Unknown"
                primary_common = "Unknown"
            return multiplier, clean_name, family, primary_common
        elif score < 0.8 and score > 0.5:
            multiplier = 0.75
            if isinstance(species, dict):
                # Family
                family_field = species.get('family')
                if isinstance(family_field, dict):
                    family = family_field.get('scientificName', 'Unknown')
                else:
                    family = family_field or "Unknown"

                # Common names
                common_names = species.get('commonNames', [])
                primary_common = common_names[0] if common_names else "Unknown"

            # Case 2: species is a string (only scientific name returned)
            elif isinstance(species, str):
                family = "Unknown"
                primary_common = species  # fallback to scientific name

            else:
                family = "Unknown"
                primary_common = "Unknown"
            return multiplier, clean_name, family, primary_common
        else:
            multiplier = 0.45
            if isinstance(species, dict):
                # Family
                family_field = species.get('family')
                if isinstance(family_field, dict):
                    family = family_field.get('scientificName', 'Unknown')
                else:
                    family = family_field or "Unknown"

                # Common names
                common_names = species.get('commonNames', [])
                primary_common = common_names[0] if common_names else "Unknown"

            # Case 2: species is a string (only scientific name returned)
            elif isinstance(species, str):
                family = "Unknown"
                primary_common = species  # fallback to scientific name

            else:
                family = "Unknown"
                primary_common = "Unknown"
            return multiplier, clean_name, family, primary_common
    else:
        if score > 0.8:
            multiplier = 1
            return multiplier, clean_name
        elif score < 0.8 and score > 0.5:
            multiplier = 0.75
            return multiplier, clean_name
        else:
            multiplier = 0.45
            return multiplier, clean_name