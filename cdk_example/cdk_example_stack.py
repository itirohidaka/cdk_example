from aws_cdk import (
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_iam as iam,    
    aws_eks as eks,
    aws_ecr as ecr,
    core
)

class CdkExampleStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # The code that defines your stack goes here
        # Creating a basic S3 bucket (versioned and without public access)
        bucket = s3.Bucket(self, "testeitiro",
            bucket_name="itirobucketteste",
            versioned=False,
            removal_policy=core.RemovalPolicy.DESTROY,
            public_read_access=False)

        # Creating a new VPC
        vpc = ec2.Vpc(self, "VPC",
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(name="public",cidr_mask=24,subnet_type=ec2.SubnetType.PUBLIC),
                ec2.SubnetConfiguration(name="private",cidr_mask=24,subnet_type=ec2.SubnetType.PRIVATE) ],
            )

        # Defining the AMI 
        amzn_linux = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
            )
            
        # Creating a new security group
        my_security_group = ec2.SecurityGroup(self, "SecurityGroup",
            vpc=vpc,
            description="Allow ssh access to ec2 instances",
            allow_all_outbound=True
        )
        my_security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "allow ssh access from the world")
        my_security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "allow http access from the world")
        my_security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "allow https access from the world")

        # Instance Role and SSM Managed Policy
        role = iam.Role(self, "InstanceSSM", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2RoleforSSM"))

        with open("./userdata/configure.sh") as f:
            user_data = f.read()
        
        # Creating a new EC2 instance
        inst_subnet = ec2.SubnetSelection(subnet_name="public")
        
        instance = ec2.Instance(self, "Instance123",
            instance_type=ec2.InstanceType("t3.nano"),
            machine_image=amzn_linux,
            security_group = my_security_group,
            vpc = vpc,
            role = role,
            key_name = "itirohome",
            user_data=ec2.UserData.custom(user_data),
            vpc_subnets=inst_subnet,
        )
        
        #Creating a EKS Cluster and Fargate Profile
        k8s1 = eks.Cluster(self, "CDKcluster1",
            cluster_name="CDKEKS-1",
            version=eks.KubernetesVersion.V1_17, 
            vpc=vpc
        )
        
        k8s1.add_fargate_profile("MyProfile",
            selectors=[{"namespace": "fargate"}]
        )
        
        #Creating a Elastic Container Registry (ECR) repository
        repository = ecr.Repository(self, "cdkrepo",
            image_scan_on_push=True,
            repository_name="cdkrepo"
        )

        # The code that defines your stack goes here
