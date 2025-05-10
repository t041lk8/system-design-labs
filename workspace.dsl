workspace {
    name "Service Ordering Website"
    description "A web application for ordering various services"

    model {
        customer = person "Customer" "A user who can browse and order services"
        admin = person "Administrator" "A user who manages services and users"

        serviceOrderingSystem = softwareSystem "ServiceOrderingWebsite" {
            description "Allows users to browse and order services"

            apiApp = container "API Application" {
                description "Handles all business logic and data access via REST API"
                technology "FastAPI"
                tags "api-application"

                userModel = component "User Model" {
                    description "Represents user data structure and operations"
                    technology "Pydantic"
                }

                serviceModel = component "Service Model" {
                    description "Represents service data structure and operations"
                    technology "Pydantic"
                }

                orderModel = component "Order Model" {
                    description "Represents order data structure and operations"
                    technology "Pydantic"
                }
            }

            database = container "Database" {
                description "Stores user, service, and order data and provides search functionality"
                technology "PostgreSQL"
                tags "database"
            }
        }

        customer -> serviceOrderingSystem "Uses"
        admin -> serviceOrderingSystem "Manages"

        # Define relationships between customer and containers
        customer -> apiApp "Makes REST API calls to"

        # Define relationships between admin and containers
        admin -> apiApp "Manages via REST API"
        admin -> database "Manages"

        # Define relationships between containers
        apiApp -> database "Reads from, writes to, and searches via SQL"

        # Define relationships between components
        userModel -> database "Stores and retrieves user data"
        serviceModel -> database "Stores and retrieves service data"
        orderModel -> database "Stores and retrieves order data"
    }

    views {
        systemContext serviceOrderingSystem "SystemContext" {
            include *
        }

        container serviceOrderingSystem "Containers" {
            include *
        }

        component apiApp "Components" {
            include *
        }

        dynamic serviceOrderingSystem "UserManagement" "Shows user management operations" {
            title "User Management"

            customer -> apiApp "POST /users - Creates new user"
            apiApp -> database "Stores user data"
            database -> apiApp "Confirms user creation"
            apiApp -> customer "Returns user details"

            customer -> apiApp "GET /users/{login} - Searches user by login"
            apiApp -> database "Queries user by login"
            database -> apiApp "Returns user data"
            apiApp -> customer "Returns user details"

            customer -> apiApp "GET /users/search?name={mask} - Searches user by name mask"
            apiApp -> database "Queries users by name pattern"
            database -> apiApp "Returns matching users"
            apiApp -> customer "Returns user list"
        }

        dynamic serviceOrderingSystem "ServiceManagement" "Shows service management operations" {
            title "Service Management"

            customer -> apiApp "POST /services - Creates new service"
            apiApp -> database "Stores service data"
            database -> apiApp "Confirms service creation"
            apiApp -> customer "Returns service details"

            customer -> apiApp "GET /services - Requests service list"
            apiApp -> database "Retrieves services"
            database -> apiApp "Returns services"
            apiApp -> customer "Returns service list"
        }

        dynamic serviceOrderingSystem "OrderManagement" "Shows order management operations" {
            title "Order Management"

            customer -> apiApp "GET /services - Requests available services"
            apiApp -> database "Retrieves services"
            database -> apiApp "Returns services"
            apiApp -> customer "Returns services"

            customer -> apiApp "POST /orders - Creates order"
            apiApp -> database "Stores order"
            database -> apiApp "Confirms order creation"
            apiApp -> customer "Confirms order"

            customer -> apiApp "PUT /orders/{orderId}/services - Adds services to order"
            apiApp -> database "Updates order with services"
            database -> apiApp "Confirms service addition"
            apiApp -> customer "Confirms updated order"

            customer -> apiApp "GET /orders/{orderId} - Requests order details"
            apiApp -> database "Retrieves order"
            database -> apiApp "Returns order data"
            apiApp -> customer "Returns order details"
        }

        styles {
            element "Person" {
                shape Person
                background #08427B
                color #ffffff
            }
            element "Software System" {
                background #1168BD
                color #ffffff
            }
            element "Container" {
                background #438DD5
                color #ffffff
            }
            element "Component" {
                background #85BBF0
                color #000000
            }
            element "Database" {
                shape Cylinder
            }
        }
    }
}