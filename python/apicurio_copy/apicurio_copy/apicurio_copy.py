"""apicurio_copy.apicurio_copy: provides entry point main()."""

import argparse
from schema_registry.client import SchemaRegistryClient
from schema_registry.client.utils import SchemaVersion

def parse_args():
    argparser = argparse.ArgumentParser(description='Copy avro schema from source to destination')
    argparser.add_argument('--source-schema', required=True, help='source schema registry uri')
    argparser.add_argument('--dest-schema', required=True, help='destination schema registry uri')
    argparser.add_argument('--source-subject', required=True, help='the subject to copy from')
    argparser.add_argument('--source-version', required=False, default="latest", help='the subject version that needs to be copied. default: latest')
    argparser.add_argument('--dest-subject', required=False, help='the subject to copy to')
    return argparser.parse_args()

def main():
    args = parse_args()
    source_registry = SchemaRegistryClient(args.source_schema)
    dest_registry = SchemaRegistryClient(args.dest_schema)
    source_schema: SchemaVersion = source_registry.get_schema(subject=f"{args.source_subject}",version=f"{args.source_version}")
    if source_schema is None:
        print(f"source subject [{args.source_subject}:{args.source_version}] was not found")
        exit(1)
    
    try:
        dest_subect = args.source_subject if args.dest_subject is None else args.dest_subject
        dest_schema_id = dest_registry.register(subject=dest_subect, schema=source_schema.schema)
        print(f"Created schema id [{dest_schema_id}] for subject [{dest_subect}]")
    except Exception as e:
        print(F"Error creating the subject [{dest_subect}]: [{str(e)}]")
        exit(1)
    
if __name__ == '__main__':
    main()