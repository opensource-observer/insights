import json
import os
import requests
import time
from typing import List, Dict, Optional
from urllib.parse import urlparse


SCHEMAS = [
    ("0xfdcfdad2dbe7489e0ce56b260348b7f14e8365a8a325aef9834818c00d46b31b", "RetroFunding_BadgeholderAttestations"),
    ("0xc9bc703e3c48be23c1c09e2f58b2b6657e42d8794d2008e3738b4ab0e2a3a8b6", "MGL_ImpactAttestations"),
    # ("0x88b62595c76fbcd261710d0930b5f1cc2e56758e155dea537f82bf0baadd9a32", "RetroFunding_ApplicationAttestations"),
    # ("0x7ae9f4adabd9214049df72f58eceffc48c4a69e920882f5b06a6c69a3157e5bd", "RetroFunding_ProjectAttestations"),
    # ("0xe035e3fe27a64c8d7291ae54c6e85676addcbc2d179224fe7fc1f7f05a8c6eac", "RetroFunding_ProjectMetadataAttestations"),
    # ("0x3743be2afa818ee40304516c153427be55931f238d961af5d98653a93192cdb3", "RetroFunding_ContributionAttestations"),
    ("0xef874554718a2afc254b064e5ce9c58c9082fb9f770250499bf406fc112bd315", "Governance_CouncilAttestations")
]

class EASSchema:
    def __init__(self, schema_id: str, json_path: str):
        self.schema_id = schema_id
        self.json_path = json_path
        self.url = 'https://optimism.easscan.org/graphql'
        self.query_limit = 100

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
            return response.json()
        
        if response.status_code == 429:
            time.sleep(sleep)
            return EASSchema.get_metadata(uri, tries=tries+1)
        
        else:
            print(f"Error {response.status_code} at {uri}")
            return None
        

    @staticmethod
    def is_valid_uri(uri: str) -> bool:
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
            if self.is_valid_uri(obj_value):
                print(f"Found URI in field '{obj_name}': {obj_value}")
                metadata = self.get_metadata(obj_value)
                if metadata:
                    attestation_data['metadata'] = metadata
        return attestation_data


    def fetch_and_dump(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r') as f:
                data = json.load(f)
            start_time = max(a['timeCreated'] for a in data)
        else:
            data = []
            start_time = 0
        
        attestations = self.fetch_attestations(time_created_after=start_time)
        if not attestations:
            return
        
        for a in attestations:
            if a['revocationTime']:
                continue
            attestation_data = self.process_attestation(a)
            if attestation_data:
                data.append(attestation_data)
                
        with open(self.json_path, "w") as f:
            json.dump(data, f, indent=2)


if __name__ == "__main__":
    for (schema_id, schema_name) in SCHEMAS:
        print(f"\nFetching attestations for {schema_name} at https://optimism.easscan.org/schema/view/{schema_id}")
        schema = EASSchema(
            schema_id=schema_id,
            json_path=f"data/{schema_name}.json"
        )
        schema.fetch_and_dump()
