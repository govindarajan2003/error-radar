import json
import requests
import time

# Base URL of your running FastAPI app
API_URL = "http://127.0.0.1:8000"

# Realistic human fixes mapped by error ID
FIXES = {
    74: "Added a null-safety check on the line string input before calling .trim() at line 42 in UserService.java. If the incoming user profile data contains a null or missing line value, the code now handles it gracefully (defaulting to an empty string) instead of throwing a NullPointerException",
    75: "Added a null validation check for paymentRequest at the start of the validate method in PaymentValidator.java:88. If the request object itself payload comes in null, it now rejects the validation early with an invalid request exception instead of throwing a generic NPE when trying to read the card number field.",
    76: "Navigated to line 67 in InvoiceGenerator.java. The order object wasn't being verified before pulling its ID. Added an intentional conditional check to verify the order model exists first. If it's empty, we log a warning pipeline block and skip invoice creation for that sequence entry.",
    77: "Fixed the missing check on the raw email string in NotificationService.java:101. Before forcing .toLowerCase(), added a guard clause using StringUtils.hasText() so that null or entirely blank addresses are filtered out immediately.",
    78: "Wrapped line 53 of CustomerParser.java in an optional check. If the parent Address object is missing from the inbound payload payload, the parser defaults the city field to an empty string instead of causing an unexpected NullPointerException.",
    79: "Increased the Hikari connection pool timeout window from default to 30000ms. Also optimized the underlying complex indexing configurations on our active database tables to prevent heavy authorization routines from locking up connections.",
    80: "Investigated network rules for the order service pod. Updated the JDBC application environment properties to target the correct internal container port and confirmed the PostgreSQL server configuration allows connections from this microservice subnet.",
    81: "The connection pool was bottlenecking under spike traffic loads. Bumped maximum-pool-size to 25 within the database properties file and ensured all data streams explicitly invoke .close() inside a finally block to free connections back to HikariCP.",
    82: "Refactored the heavy analytics aggregation script. Replaced raw sequential scanning blocks with an optimized compound execution pattern, and added specific PostgreSQL table indexes on the date ranges to bring execution time well below the 30-second driver constraint threshold.",
    83: "Implemented an explicit capture block handling ExpiredJwtException at the API Gateway middleware engine stage. Instead of dropping the request roughly, it now redirects safely to the token refresh execution loop.",
    84: "Caught the raw AuthenticationException safety flag within AuthController.java:72. This cleanly returns a descriptive message to the security client context rather than allowing a structural core error cascade to reach the user.",
    85: "Updated the environment key rotation synchronization protocol across clusters. The gateway was occasionally verifying signatures using outdated public key definitions when rotating tokens.",
    86: "Modified UserRepository.java:44 to return an Optional<User> entity block. If a queried query ID doesn't hit a match inside PostgreSQL, it maps down gracefully to a clean exception structure rather than dumping raw runtime failures.",
    87: "Added custom validation layers inside ProductService.java:89. If an unknown SKU identifier is submitted to the application backend engine, it outputs a readable domain response status indicating catalog mismatch.",
    88: "Patched OrderService.java:110 to safely catch missing sequence entries. If an out-of-bounds or archived ID payload is queried, the user tracking framework delivers an expected domain response value.",
    89: "Memory profiling indicated that generating massive historical raw reports at line 215 was holding too many rows in the local heap segment. Refactored the core report service loop to stream batch rows using database pagination instead of pulling everything into memory at once.",
    90: "Eviction policies on our localized structural caching data maps were configured too tightly, trapping references indefinitely. Refactored CacheManager.java:188 to aggressively wipe dirty references via fixed time-to-live settings.",
    91: "The worker background loop was spawning unbound OS native threads blindly under load conditions. Swapped the architecture model around line 95 to share a managed, fixed-size standard Python/Java thread executor system.",
    92: "Corrected a faulty type coercion mapping error inside RequestMapper.java:73. Incoming string numeric characters from json payloads are now formally parsed using Integer.valueOf() instead of performing an immediate direct variable casting wrapper.",
    93: "Fixed an unbounded recursive depth pattern during multi-layered data parsing processing inside RecursiveParser.java:34. Added a strict maximum constraint threshold iteration validation counter to drop processing early if an infinite loop signature is encountered."
}

def seed_database_fixes():
    print("Initializing error database seeding script...")
    
    success_count = 0
    fail_count = 0

    for error_id, description in FIXES.items():
        # Build the exact endpoint string
        endpoint = f"{API_URL}/errors/{error_id}/fix"
        
        # Match Pydantic's FixRequest schema model attribute name
        payload = {
            "fix_description": description
        }
        print(endpoint)
        try:
            response = requests.post(endpoint, json=payload, timeout=5)
            
            if response.status_code == 200:
                print(f"Success [ID {error_id}]: API accepted resolution data successfully.")
                success_count += 1
            else:
                print(f"Failed  [ID {error_id}]: API returned HTTP {response.status_code} - {response.text}")
                fail_count += 1
                
        except requests.exceptions.RequestException as req_err:
            print(f"Network Crash [ID {error_id}]: Could not connect to API server. Details: {req_err}")
            fail_count += 1
            
        # Subtle sleep to prevent hammering local process context
        time.sleep(0.05)

    print("\n--- Seeding Statistics ---")
    print(f"Total Successful submissions: {success_count}")
    print(f"Total Failed submissions: {fail_count}")

if __name__ == "__main__":
    seed_database_fixes()