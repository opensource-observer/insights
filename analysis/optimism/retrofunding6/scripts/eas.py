import json
import os
import pandas as pd
import requests
import time
from typing import List, Dict, Optional
from urllib.parse import urlparse


SCHEMA_LIST = [
    ("0xff0b916851c1c5507406cfcaa60e5d549c91b7f642eb74e33b88143cae4b47d0", "Entity", 594),
    ("0xe035e3fe27a64c8d7291ae54c6e85676addcbc2d179224fe7fc1f7f05a8c6eac", "Project Metadata Snapshot", 472),
    ("0xc2b376d1a140287b1fa1519747baae1317cf37e0d27289b86f85aa7cebfd649f", "Organization Metadata Snapshot", 595),
    ("0x2169b74bfcb5d10a6616bbc8931dc1c56f8d1c305319a9eeca77623a991d4b80", "RetroFunding Application (RF6)", 609),
    ("0x88b62595c76fbcd261710d0930b5f1cc2e56758e155dea537f82bf0baadd9a32", "RetroFunding Application V1", 470),
    ("0x41513aa7b99bfea09d389c74aacedaeb13c28fb748569e9e2400109cbe284ee5", "Round 5 Badgeholder", 599),
    ("0xef874554718a2afc254b064e5ce9c58c9082fb9f770250499bf406fc112bd315", "Governance_CouncilAttestations", 141),
    ("0xc9bc703e3c48be23c1c09e2f58b2b6657e42d8794d2008e3738b4ab0e2a3a8b6", "MGL Impact Attestation", 566)
]

DEPRECATED_LIST = [
    ("0x7ae9f4adabd9214049df72f58eceffc48c4a69e920882f5b06a6c69a3157e5bd", "Project v1", 473),
    ("0x0e5d439a46d50507c63ea277b75c4d87711cc9d1754103393066927ee9be9fe3", "Project v0", 427),
    ("0x9a384502b07bb8dfe65a784d0abee1dc22ff541024a9965d78ef7934dda7b6ca", "Project Metadata Snapshot v0", 428),
    ("0x5a2187bc9d5f9a35b18538f30614ea92fc31c7f704707161de395f2ce6c09cab", "RetroFunding Application v0", 429),
    ("0x3743be2afa818ee40304516c153427be55931f238d961af5d98653a93192cdb3", "RetroFunding Contribution", 243),
    ("0xfdcfdad2dbe7489e0ce56b260348b7f14e8365a8a325aef9834818c00d46b31b", "Round 4 Badgeholder", 78),    
    ("0x0de72a1e3d38bf069bce8e5b705dbf8421f921a830b046a6605d6050d1760dcd", "MGL Project Registry", 565)
]


class EASSchema:
    def __init__(self, name: str, schema_id: str, json_path: str):
        self.name = name
        self.schema_id = schema_id
        self.json_path = json_path
        self.url = 'https://optimism.easscan.org/graphql'
        self.query_limit = 100
        self.data = []

    def fetch_attestations(self, time_created_after: int = 0) -> List[Dict]:
        query = '''
        query Attestations($schemaId: StringFilter!, $skip: Int!, $take: Int!, $timeCreatedAfter: IntFilter) {
            attestations(where: {schemaId: $schemaId, timeCreated: $timeCreatedAfter}, take: $take, skip: $skip) {
                id
                attester
                recipient
                refUID
                revocable
                revocationTime
                expirationTime
                timeCreated 
                decodedDataJson    
            }
        }
        '''
        
        variables = {
            "schemaId": {"equals": self.schema_id},
            "skip": 0,
            "take": self.query_limit,
            "timeCreatedAfter": {"gt": time_created_after},
        }

        headers = {'Content-Type': 'application/json'}
        all_attestations = []

        while True:
            payload = {'query': query, 'variables': variables}

            try:
                response = requests.post(self.url, headers=headers, data=json.dumps(payload))
                response.raise_for_status()

                data = response.json()
                attestations = data.get('data', {}).get('attestations', [])
                all_attestations.extend(attestations)

                if len(attestations) < self.query_limit:
                    break

                variables["skip"] += self.query_limit

            except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                print(f"Failed to fetch attestations for {self.schema_id}: {str(e)}")
                break

        print(f"Total attestations for Schema ID {self.schema_id}: {len(all_attestations)}")
        return all_attestations


    @staticmethod
    def get_metadata(uri: str, tries: int = 0, headers: Dict = {}, sleep: int = 180) -> Optional[Dict]:
        if tries == 3:
            print("Too many tries.")
            return None

        response = requests.get(uri, headers=headers)
        if response.status_code == 200:
            try:
                return response.json()
            except:
                print("No json at:", uri)
                return None
        
        if response.status_code == 429:
            time.sleep(sleep)
            return EASSchema.get_metadata(uri, tries=tries+1)
        
        else:
            print(f"Error {response.status_code} at {uri}")
            return None
        

    @staticmethod
    def is_valid_uri(uri: str) -> bool:
        if uri[:4] != 'http':
            return False
        try:
            result = urlparse(uri)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False
        

    def process_attestation(self, a: Dict) -> Optional[Dict]:
        attestation_data = {
            'id': a['id'],
            'attester': a['attester'],
            'recipient': a['recipient'],
            'timeCreated': a['timeCreated']
        }
        decoded_json = json.loads(a['decodedDataJson'])
        for obj in decoded_json:
            obj_name = obj['name']
            obj_value = obj['value']['value']
            attestation_data[obj_name] = obj_value
            if isinstance(obj_value, str) and self.is_valid_uri(obj_value):
                print(f"Found URI in field '{obj_name}': {obj_value}")
                metadata = self.get_metadata(obj_value)
                if metadata:
                    attestation_data['metadata'] = metadata
        return attestation_data


    def fetch_and_dump(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r') as f:
                self.data = json.load(f)
            start_time = max(a['timeCreated'] for a in self.data)
        else:
            self.data = []
            start_time = 0
        
        attestations = self.fetch_attestations(time_created_after=start_time)
        if not attestations:
            return
        
        for a in attestations:
            if a['revocationTime']:
                continue
            attestation_data = self.process_attestation(a)
            if attestation_data:
                self.data.append(attestation_data)
                
        with open(self.json_path, "w") as f:
            json.dump(self.data, f, indent=2)

    def get_data(self):
        return self.data

    def load_data(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r') as f:
                self.data = json.load(f)
        else:
            print(f"No data file found at {self.json_path}")

    @staticmethod
    def convert_farcaster_id(farcaster_id):
        return int(farcaster_id['hex'], 16) if farcaster_id else None

    def clean_data(self):
        if self.data:
            for a in self.data:
                a['timeCreated'] = pd.to_datetime(a['timeCreated'], unit='s')
                a['attester'] = a['attester'].lower()
                a['recipient'] = a['recipient'].lower()
                if 'farcasterID' in a:
                    a['farcasterID'] = self.convert_farcaster_id(a['farcasterID'])


if __name__ == "__main__":
    for (schema_id, schema_name, schema_num) in SCHEMA_LIST:
        schema_url = f"https://optimism.easscan.org/schema/view/{schema_id}"
        print(f"\nFetching attestations for {schema_name} at {schema_url}")
        try:
            schema = EASSchema(
                name=schema_name,
                schema_id=schema_id,
                json_path=f"data/attestations/{schema_num}.json"
            )
            schema.fetch_and_dump()
            schema.clean_data()
        except Exception as e:
            print(f"Failed to fetch attestations for {schema_num}: {schema_name}: {str(e)}")
