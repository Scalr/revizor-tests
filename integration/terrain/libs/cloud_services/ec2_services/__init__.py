import api_gateway
import cognito_identity
import cognito_user_pools
import device_farm
import dynamodb
import ecs
import glacier
import lmbda
import mobile
import pinpoint
import redshift
import route53
import ses
import sns
import sqs


services = {
    api_gateway.ApiGateway.service_name: api_gateway.ApiGateway,
    cognito_identity.CognitoIdentity.service_name: cognito_identity.CognitoIdentity,
    cognito_user_pools.CognitoUserPools.service_name: cognito_user_pools.CognitoUserPools,
    device_farm.DeviceFarm.service_name: device_farm.DeviceFarm,
    dynamodb.DynamoDb.service_name: dynamodb.DynamoDb,
    ecs.Ecs.service_name: ecs.Ecs,
    glacier.Glacier.service_name: glacier.Glacier,
    lmbda.Lambda.service_name: lmbda.Lambda,
    mobile.Mobile.service_name: mobile.Mobile,
    pinpoint.Pinpoint.service_name: pinpoint.Pinpoint,
    redshift.Redshift.service_name: redshift.Redshift,
    route53.Route53.service_name: route53.Route53,
    ses.Ses.service_name: ses.Ses,
    sns.Sns.service_name: sns.Sns,
    sqs.Sqs.service_name: sqs.Sqs
}
