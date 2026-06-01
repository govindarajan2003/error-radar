import os
from dotenv import load_dotenv
from sqlalchemy import text, create_engine
from services.embedding_service import embed_error

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

seed_errors = [

    # =========================================================
    # NullPointerException Errors
    # =========================================================

    {
        "message": "Null pointer while processing user profile",
        "stack_trace": 'java.lang.NullPointerException: Cannot invoke "String.trim()" because "line" is null at UserService.java:42',
        "sanitized_trace": "NullPointerException while processing user profile due to null line value",
        "service_name": "user-service"
    },

    {
        "message": "Null pointer during payment validation",
        "stack_trace": 'java.lang.NullPointerException: Cannot read field "cardNumber" because "paymentRequest" is null at PaymentValidator.java:88',
        "sanitized_trace": "NullPointerException during payment validation because payment request object was null",
        "service_name": "payment-service"
    },

    {
        "message": "Null pointer while generating invoice",
        "stack_trace": 'java.lang.NullPointerException: Cannot invoke "Order.getId()" because "order" is null at InvoiceGenerator.java:67',
        "sanitized_trace": "NullPointerException while generating invoice due to missing order object",
        "service_name": "invoice-service"
    },

    {
        "message": "Null pointer in email notification flow",
        "stack_trace": 'java.lang.NullPointerException: Cannot invoke "String.toLowerCase()" because "email" is null at NotificationService.java:101',
        "sanitized_trace": "NullPointerException during email notification because email value was null",
        "service_name": "notification-service"
    },

    {
        "message": "Null pointer while parsing customer address",
        "stack_trace": 'java.lang.NullPointerException: Cannot invoke "Address.getCity()" because "address" is null at CustomerParser.java:53',
        "sanitized_trace": "NullPointerException while parsing customer address due to null address object",
        "service_name": "customer-service"
    },

    # =========================================================
    # Database Errors 
    # =========================================================

    {
        "message": "Database connection timeout",
        "stack_trace": "org.postgresql.util.PSQLException: Connection attempt timed out at HikariPool.java:215",
        "sanitized_trace": "Database connection timeout while connecting to PostgreSQL",
        "service_name": "auth-service"
    },

    {
        "message": "PostgreSQL connection refused",
        "stack_trace": "java.sql.SQLException: Connection refused at PostgreSQLDriver.java:302",
        "sanitized_trace": "Database connection refused by PostgreSQL server",
        "service_name": "order-service"
    },

    {
        "message": "Database connection pool exhausted",
        "stack_trace": "com.zaxxer.hikari.pool.HikariPool$PoolInitializationException: Connection pool exhausted at HikariPool.java:480",
        "sanitized_trace": "Database connection pool exhausted in HikariCP",
        "service_name": "inventory-service"
    },

    {
        "message": "SQL query execution timeout",
        "stack_trace": "java.sql.SQLTimeoutException: Query timed out after 30000ms at PreparedStatement.java:210",
        "sanitized_trace": "SQL query execution timeout after prolonged database operation",
        "service_name": "analytics-service"
    },

    # =========================================================
    # Authentication Errors 
    # =========================================================

    {
        "message": "JWT token expired",
        "stack_trace": "io.jsonwebtoken.ExpiredJwtException: JWT expired at JwtParser.java:145",
        "sanitized_trace": "Authentication failed because JWT token expired",
        "service_name": "gateway-service"
    },

    {
        "message": "Invalid login credentials",
        "stack_trace": "com.security.AuthenticationException: Invalid username or password at AuthController.java:72",
        "sanitized_trace": "Authentication failed due to invalid user credentials",
        "service_name": "auth-service"
    },

    {
        "message": "JWT signature verification failed",
        "stack_trace": "io.jsonwebtoken.SignatureException: JWT signature does not match locally computed signature at JwtVerifier.java:61",
        "sanitized_trace": "Authentication failed because JWT signature verification failed",
        "service_name": "gateway-service"
    },

    # =========================================================
    # Not Found Errors 
    # =========================================================

    {
        "message": "User record not found",
        "stack_trace": "com.app.UserNotFoundException: User with id 101 not found at UserRepository.java:44",
        "sanitized_trace": "Requested user resource was not found in database",
        "service_name": "user-service"
    },

    {
        "message": "Product not found",
        "stack_trace": "com.app.ProductNotFoundException: Product SKU-991 not found at ProductService.java:89",
        "sanitized_trace": "Requested product resource was not found",
        "service_name": "catalog-service"
    },

    {
        "message": "Order not found",
        "stack_trace": "com.app.OrderNotFoundException: Order id 5002 not found at OrderService.java:110",
        "sanitized_trace": "Requested order resource was not found",
        "service_name": "order-service"
    },

    # =========================================================
    # Memory Errors 
    # =========================================================

    {
        "message": "Java heap space exhausted",
        "stack_trace": "java.lang.OutOfMemoryError: Java heap space at ReportGenerator.java:215",
        "sanitized_trace": "Application ran out of Java heap memory during report generation",
        "service_name": "report-service"
    },

    {
        "message": "GC overhead limit exceeded",
        "stack_trace": "java.lang.OutOfMemoryError: GC overhead limit exceeded at CacheManager.java:188",
        "sanitized_trace": "Garbage collector overhead exceeded memory limits",
        "service_name": "cache-service"
    },

    {
        "message": "Unable to create native thread",
        "stack_trace": "java.lang.OutOfMemoryError: unable to create new native thread at WorkerPool.java:95",
        "sanitized_trace": "Application failed to create additional native threads due to memory exhaustion",
        "service_name": "worker-service"
    },

    # =========================================================
    # Unexpected Errors 
    # =========================================================

    {
        "message": "Class cast exception during request mapping",
        "stack_trace": "java.lang.ClassCastException: java.lang.String cannot be cast to java.lang.Integer at RequestMapper.java:73",
        "sanitized_trace": "ClassCastException caused by invalid type conversion during request mapping",
        "service_name": "api-service"
    },

    {
        "message": "Recursive method caused stack overflow",
        "stack_trace": "java.lang.StackOverflowError at RecursiveParser.java:34",
        "sanitized_trace": "StackOverflowError caused by uncontrolled recursive method calls",
        "service_name": "parser-service"
    }
]

for error in seed_errors:
    with engine.connect() as connection:
        query = text("SELECT id from errors where message = :message and sanitized_trace = :sanitized_trace;")
        result = connection.execute(query,{
            "message": error.get('message'),
            "sanitized_trace": error.get('sanitized_trace'),
        })
    if result.fetchone():
        print("Skipped")
        continue
    with engine.begin() as connection:
        query = text(""" INSERT INTO errors (message, stack_trace, sanitized_trace, service_name)
            VALUES (:message, :stack_trace, :sanitized_trace, :service_name)
            RETURNING id;
        """)
        id = connection.execute(query,{
            "message": error.get('message'),
            "stack_trace": error.get('stack_trace'),
            "sanitized_trace": error.get('sanitized_trace'),
            "service_name": error.get('service_name'),
        }).scalar()
    embed_error(id, error.get('sanitized_trace'))
    