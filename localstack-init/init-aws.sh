#!/bin/bash
export AWS_DEFAULT_REGION=eu-south-1
echo "Inizializzazione risorse LocalStack in region $AWS_DEFAULT_REGION..."

# 1. Crea Topic SNS
echo "Creazione SNS Topic..."
TOPIC_ARN=$(awslocal sns create-topic --name fantacloud-match-notifications --query 'TopicArn' --output text)
echo "SNS Topic creato: $TOPIC_ARN"

# 2. Crea SQS Queue
echo "Creazione SQS Queue..."
QUEUE_URL=$(awslocal sqs create-queue --queue-name fantacloud-matchday-calculated --query 'QueueUrl' --output text)
QUEUE_ARN=$(awslocal sqs get-queue-attributes --queue-url $QUEUE_URL --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)
echo "SQS Queue creata: $QUEUE_URL"

# 3. Prepara la Lambda
echo "Zippando la lambda..."
cd /lambdas
zip lambda_notify_matchday.zip lambda_notify_matchday.py
cd /

# 4. Crea la Lambda
echo "Creazione Lambda function..."
awslocal lambda create-function \
    --function-name LambdaNotifyMatchday \
    --runtime python3.11 \
    --handler lambda_notify_matchday.lambda_handler \
    --role arn:aws:iam::000000000000:role/lambda-role \
    --zip-file fileb:///lambdas/lambda_notify_matchday.zip \
    --environment Variables="{SNS_TOPIC_ARN=$TOPIC_ARN,SMTP_HOST=mailhog,DB_HOST=postgres_database,DB_NAME=projectdb,DB_USER=postgres,DB_PASSWORD=mypassword,DB_PORT=5432}"

# 5. Mappa SQS alla Lambda
echo "Creazione Event Source Mapping (SQS -> Lambda)..."
awslocal lambda create-event-source-mapping \
    --function-name LambdaNotifyMatchday \
    --batch-size 1 \
    --event-source-arn $QUEUE_ARN

echo "Inizializzazione completata!"
