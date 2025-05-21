db = db.getSiblingDB('service_db');

// Clear existing collections
db.services.drop();
db.orders.drop();

// Insert services
db.services.insertMany([
    {
        id: "86b423fd-950c-4052-b4ca-4933b88da587",
        name: "Покраска обоев",
        description: "Покаршу обои недорого",
        price: 100.00,
        created_at: new Date()
    },
    {
        id: "ee720ea8-c166-4d0e-98a0-f48d169022b2",
        name: "Пишу лабы",
        description: "Сделаю лабы по программной инженерии",
        price: 12000.00,
        created_at: new Date()
    },
    {
        id: "45578523-f257-484d-97b3-ddb9092a0121",
        name: "Фотографирую на заказ",
        description: "Профессиональный фотограф из ПГТ Бобруйск",
        price: 500.00,
        created_at: new Date()
    },
    {
        id: "9100e555-a198-45d6-83c2-49ae8ef52cc0",
        name: "Профессиональный игрок в CS2",
        description: "Выиграю любые матчи в контр страйк",
        price: 1300.00,
        created_at: new Date()
    }
]);

// Insert orders
db.orders.insertMany([
    {
        id: "d235ab9c-0213-4600-bb6f-21bed122aa24",
        user_id: "admin",
        services: [
            "86b423fd-950c-4052-b4ca-4933b88da587",
            "45578523-f257-484d-97b3-ddb9092a0121",
            "9100e555-a198-45d6-83c2-49ae8ef52cc0"
        ],
        total_price: 800.00,
        created_at: new Date()
    },
    {
        id: "a5997eee-6bf7-4190-85da-d7427acdfcad",
        user_id: "iazhbanov",
        services: [
            "86b423fd-950c-4052-b4ca-4933b88da587",
            "45578523-f257-484d-97b3-ddb9092a0121"
        ],
        total_price: 550.00,
        created_at: new Date()
    },
    {
        id: "7fe39bc9-d372-40d5-8958-5caef2e98934",
        user_id: "natasha",
        services: [
            "86b423fd-950c-4052-b4ca-4933b88da587",
            "9100e555-a198-45d6-83c2-49ae8ef52cc0",
            "ee720ea8-c166-4d0e-98a0-f48d169022b2"
        ],
        total_price: 1050.00,
        created_at: new Date()
    }
]); 