import asyncio
from db.kafka_client import get_kafka_consumer
from db.mongodb import create_service, ServiceMongo
from db.redis_client import redis_client
import json

async def process_service_commands():
    consumer = get_kafka_consumer()
    print("Service processor started. Waiting for messages...")
    
    for message in consumer:
        try:
            service_data = message.value
            print(f"Received service command: {service_data}")
            
            # Create service in MongoDB
            service_mongo = ServiceMongo(**service_data)
            created_service = await create_service(service_mongo)
            
            # Cache the service in Redis
            cache_key = f"service:{created_service.id}"
            await redis_client.set(
                cache_key,
                json.dumps(created_service.dict()),
                ex=3600  # Cache for 1 hour
            )
            
            print(f"Processed service command successfully: {created_service.id}")
            
        except Exception as e:
            print(f"Error processing service command: {str(e)}")

if __name__ == "__main__":
    asyncio.run(process_service_commands()) 