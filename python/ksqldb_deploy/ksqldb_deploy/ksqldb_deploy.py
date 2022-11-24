import argparse
from ksqldb_deploy.deployer.KsqldbDeployerContext import KsqldbDeployerContext
from ksqldb_deploy.deployer.KsqldbDeployer import KsqldbDeployer

def main():
    parser = argparse.ArgumentParser(description='Deploy ksqldb scripts')
    parser.add_argument('--name', required=False, default="default", help='The deployment''s name')
    parser.add_argument('--ksqldb-uri', required=True, help='The ksqldb rest endpoint uri')
    parser.add_argument('--base-scripts-path', required=True, help='The base folder containing all ksqldb scripts')
    parser.add_argument('--script', action='append', required=False, help='An optionally selected list of scripts to deploy')
    parser.add_argument('--ksqldb-var-file', action='append', required=False, help='A Yaml structure file/s to include variables to be added to the deployment')
    parser.add_argument('--broker-list', required=False, help='CSV list of brokers e.g. broker1:9092,broker2:9092,broker3:9092')
    parser.add_argument('--topic-partitions', required=False, type=int, default=None, help='The number of partitions to create when creating missing topics')
    parser.add_argument('--topic-replicas', required=False, type=int, default=None, help='The number of replicas to configure when creating missing topics')
    parser.add_argument('--schema-registry-uri', required=False, help='The optional Schema Registry uri')
    parser.add_argument('--force', required=False, action=argparse.BooleanOptionalAction, default=False, help='Force deploy all matching scripts')
    args = parser.parse_args()

    print('Deploy ksqldb scripts Starting.....')
    print('--------------------------------------------------------------------------------------------------------')
    print(f"Name: {args.name}")
    print('--------------------------------------------------------------------------------------------------------')
    print(f"Ksqldb Uri: {args.ksqldb_uri}")
    print(f"Base Scripts Path: {args.base_scripts_path}")
    print(f"Scripts: {args.script}")
    print(f"Ksqldb Variable Files: {args.ksqldb_var_file}")
    print(f"Force: {args.force}")
    print('--------------------------------------------------------------------------------------------------------')
    print(f"Brokers: {args.broker_list}")
    print(f"Topic Partitions: {args.topic_partitions}")
    print(f"Topic Replicas: {args.topic_replicas}")
    print(f"Schema Registry Uri: {args.schema_registry_uri}")
    print('--------------------------------------------------------------------------------------------------------')
    print('')

    try:
        ksql_deployer_context = KsqldbDeployerContext()
        ksql_deployer_context.name = args.name
        ksql_deployer_context.ksqldb_uri = args.ksqldb_uri
        ksql_deployer_context.schema_registry_url = args.schema_registry_uri
        ksql_deployer_context.kafka_bootstrap_servers = args.broker_list
        ksql_deployer_context.base_scripts_path = args.base_scripts_path
        ksql_deployer_context.variable_files = args.ksqldb_var_file
        ksql_deployer_context.script = args.script
        ksql_deployer_context.force = args.force
        ksql_deployer_context.topic_partitions = args.topic_partitions
        ksql_deployer_context.topic_replicas = args.topic_replicas
        
        print(F"Initialising...")
        ksql_deployer: KsqldbDeployer = KsqldbDeployer(ksql_deployer_context)
        print("")

        print(F"Loading Deployed Ksqldb Script Checksums...")
        ksql_deployer.load_ksqldb_scripts_checksums()
        print("")

        print(F"Loading Scripts Metadata...")
        ksql_deployer.load_scripts_metadata()
        print("")

        print(F"Determining Script Dependency Tree...")
        ksql_deployer.determine_scripts_deployment_plan()
        print("")

        if ksql_deployer_context.topic_partitions is not None and ksql_deployer_context.topic_replicas is not None:
            print(F"Creating Missing Kafka Topics...")
            ksql_deployer.create_missing_kafka_topics()
            print("")
        
        print(F"Dropping Existing Ksqldb Entities...")
        for ksqldb_drop_entity in ksql_deployer.get_deleting_ksqldb_entities():
            print(F"Dropping [{ksqldb_drop_entity.type}] - [{ksqldb_drop_entity.name}]")
            ksql_deployer.drop(ksqldb_drop_entity)
        print("")

        print(F"Loading Kafka Metadata...")
        ksql_deployer.load_scripts_kafka_metadata(deploy_only=True)
        print("")

        print(F"Assigning Ksqldb Variables...")
        ksql_deployer.assign_ksqldb_variables()
        print("")

        print('--------------------------------------------------------------------------------------------------------')
        print(F"Defined the following variables: -\r\n")
        print(ksql_deployer.get_variables_script())
        print('--------------------------------------------------------------------------------------------------------')

        print(F"Deploying...")
        for script in ksql_deployer.get_deployment_scripts():
            print(F"Deploying: [{script.path}]")
            ksql_deployer.deploy(script)
        print("")

    except Exception as e:
        print('--------------------------------------------------------------------------------------------------------')
        print(F"Deployment failed: [{e}]")
        print('--------------------------------------------------------------------------------------------------------')
        exit(1)

    exit(0)

if __name__ == '__main__':
    main()