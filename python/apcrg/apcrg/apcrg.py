"""apcrg.apcrg: provides entry point main()."""

import argparse
import yaml
from schema_registry.client import SchemaRegistryClient
from schema_registry.client.utils import SchemaVersion
from collections import namedtuple 

SchemaCopyContext = namedtuple("SchemaCopyContext",[
        'source_registry',
        'dest_registry',
        'source_subject',
        'source_version',
        'dest_subject'
    ])

def read_batch_config(file:str) -> any:
    with open(file, 'r') as read_file:
        return yaml.safe_load(read_file)
    
def process_cp(args: any):
    assert (args.source_schema and args.source_schema.strip()), "source schema registry uri is invalid"
    assert (args.dest_schema and args.dest_schema.strip()), "destination schema registry uri is invalid"
    
    context: SchemaCopyContext = SchemaCopyContext(
        source_registry=SchemaRegistryClient(args.source_schema),
        dest_registry=SchemaRegistryClient(args.dest_schema),
        source_subject=args.source_subject,
        source_version=args.source_version,
        dest_subject=args.dest_subject
    )
    
    copy_schema(context)
    
def process_cp_batch(args):
    assert (args.source_schema and args.source_schema.strip()), "source schema registry uri is invalid"
    assert (args.dest_schema and args.dest_schema.strip()), "destination schema registry uri is invalid"
    assert (args.file and args.file.strip()), "yaml file is invalid"
    
    batch_config = read_batch_config(args.file)
    assert "schemas" in batch_config, "yaml file does not contain an array of 'schemas'"
    
    source_registry=SchemaRegistryClient(args.source_schema)
    dest_registry=SchemaRegistryClient(args.dest_schema)
            
    for schema in batch_config.get("schemas"):
        context: SchemaCopyContext = SchemaCopyContext(
            source_registry=source_registry,
            dest_registry=dest_registry,
            source_subject=schema.get("source-subject"),
            source_version=schema.get("source-version"),
            dest_subject=schema.get("dest-subject")
        )
        
        copy_schema(context)
        
    
def parse_args():
    argparser = argparse.ArgumentParser(description='Apicurio schema registry utility set')
    subparsers = argparser.add_subparsers(help="Commands")
    
    cp = subparsers.add_parser("cp", help="Copy a single schema from source to destination")
    cp.add_argument('--source-schema', required=True, help='Source schema registry uri')
    cp.add_argument('--dest-schema', required=True, help='Destination schema registry uri')
    cp.add_argument('--source-subject', required=True, help='The subject to copy from')
    cp.add_argument('--source-version', required=False, default="latest", help='The subject version that needs to be copied. default: latest')
    cp.add_argument('--dest-subject', required=False, help='The subject to copy to')
    cp.set_defaults(func=process_cp)
    
    batch_cp = subparsers.add_parser("cp-batch", help="Reads a yaml file containing a batch of schemas to copy")
    batch_cp.add_argument('--source-schema', required=True, help='Source schema registry uri')
    batch_cp.add_argument('--dest-schema', required=True, help='Destination schema registry uri')
    batch_cp.add_argument('--file', required=True, help="The yaml file containing the list of subjects to transfer")
    batch_cp.set_defaults(func=process_cp_batch)
    return argparser.parse_args()

def copy_schema(schema_copy_context: SchemaCopyContext) -> int :
    assert schema_copy_context is not None, "schema copy context is null"
    assert schema_copy_context.source_registry is not None, "source schema registry is null"
    assert schema_copy_context.dest_registry is not None, "destination schema registry is null"
    assert (schema_copy_context.source_subject and schema_copy_context.source_subject.strip()), "source subject is invalid"
    
    source_version = "latest" if schema_copy_context.source_version is None else schema_copy_context.source_version
    dest_subject = schema_copy_context.source_subject if schema_copy_context.dest_subject is None else schema_copy_context.dest_subject
    
    print(F"copying subject [{schema_copy_context.source_subject}:{source_version}] to [{dest_subject}]")
    source_schema: SchemaVersion = schema_copy_context.source_registry.get_schema(subject=f"{schema_copy_context.source_subject}",version=f"{source_version}")
    schema_id = schema_copy_context.dest_registry.register(subject=dest_subject, schema=source_schema.schema)
    print(F" - done: [{schema_id}]")
    
    return schema_id
    
def main():
    try:
        args = parse_args()
        args.func(args)
    except Exception as e:
        print(F"Error: [{str(e)}]")
        exit(1)
    
    # source_schema: SchemaVersion = source_registry.get_schema(subject=f"{args.source_subject}",version=f"{args.source_version}")
    # if source_schema is None:
    #     print(f"source subject [{args.source_subject}:{args.source_version}] was not found")
    #     exit(1)
    
    # try:
    #     dest_subect = args.source_subject if args.dest_subject is None else args.dest_subject
    #     dest_schema_id = dest_registry.register(subject=dest_subect, schema=source_schema.schema)
    #     print(f"Created schema id [{dest_schema_id}] for subject [{dest_subect}]")
    # except Exception as e:
    #     print(F"Error creating the subject [{dest_subect}]: [{str(e)}]")
    #     exit(1)
    
if __name__ == '__main__':
    main()