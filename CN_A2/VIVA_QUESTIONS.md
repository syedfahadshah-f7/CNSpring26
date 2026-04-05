# VIVA PREPARATION - DNS Implementation (CS3001)

## Important Concepts to Understand Before VIVA

Make sure you can explain these 5-10 times clearly and concisely.

---

## 1. DNS Resolution Types

### Q1: Explain the difference between Iterative and Recursive DNS Resolution

**Answer:**


**Iterative Resolution:**
- Client makes multiple queries, one to each server
- Each server returns a referral to the next server ("try this server next")
- Client controls the resolution process
- Flow: Client -> Root -> TLD -> Authoritative
- **Key Point**: Each query is independent, client queries different server for each step

**Example Flow:**
```
Client: "Where is google.com?" -> Root
Root: "Ask the .com TLD server"
Client: "Where is google.com?" -> TLD
TLD: "Ask Google's authoritative server"
Client: "Where is google.com?" -> Authoritative
Authoritative: "64.233.187.99"
```

**Recursive Resolution:**
- Client makes ONE query to local DNS server
- Local server queries root, TLD, and authoritative on behalf of client
- Server does all the work and returns final answer
- Flow: Client -> LocalServer, then LocalServer works internally
- **Key Point**: Client makes single query; server returns complete answer

**Example Flow:**
```
Client: "Where is facebook.com?" -> LocalServer
  LocalServer: "Where is facebook.com?" -> Root
  LocalServer: "Where is facebook.com?" -> TLD
  LocalServer: "Where is facebook.com?" -> Authoritative
  LocalServer: "Here's the answer: 31.13.64.35"
LocalServer: "Here's the answer: 31.13.64.35" -> Client
```

**Key Differences Table:**

| Feature | Iterative | Recursive |
|---------|-----------|-----------|
| **Number of Client Queries** | Multiple (3-4) | One |
| **Who Controls Process** | Client | Server |
| **What Server Returns** | Referral to next server | Final answer |
| **Where Work Happens** | Distributed | At server side |
| **Example** | dig @root | dig (typical) |

---

### Q2: Show me the flow diagram for both resolution types

**Answer:**

**Iterative Resolution Diagram:**
```
CLIENT              ROOT            TLD             AUTHORITATIVE
  |                  |               |                   |
  |--Query google--->|               |                   |
  |                  |               |                   |
  |<--Referral--------|               |                   |
  |                                    |                   |
  |--Query google------>|               |                   |
  |                     |               |                   |
  |<-----Referral--------|               |                   |
  |                                                        |
  |--Query google---->|                               |
  |                                                        |
  |<------Answer: 64.233.187.99----|
```

**Recursive Resolution Diagram:**
```
CLIENT          LOCAL-SERVER        ROOT            TLD         AUTHORITATIVE
  |               |                  |               |               |
  |--Query------->|                  |               |               |
  |               |                  |               |               |
  |               |--Query root----->|               |               |
  |               |<--Referral--------|               |               |
  |               |                                    |               |
  |               |--Query TLD------->|               |               |
  |               |<-Referral----------|               |               |
  |               |                                                    |
  |               |--Query Auth----->|              |               |
  |               |<--------Answer-----+               |               |
  |               |                                                    |
  |<--Answer------|
```

---

## 2. DNS Message Format

### Q3: What is the structure of a DNS message? How is the 16-bit ID used?

**Answer:**

**DNS Message Structure:**

```
+----------------------------------+
|     Message Header (12 bytes)    |
+---------+---------+---------+-----+
| ID      | Flags   | QCount  | ANCount |
| 16 bits | 16 bits | 16 bits | 16 bits |
+---------+---------+---------+-----+
| NSCount | ARCount |
| 16 bits | 16 bits |
+---------+---------+

+----------------------------------+
|     Question Section             |
| Domain Name | Type | Class       |
+----------------------------------+

+----------------------------------+
|     Answer Section               |
| Name | Type | Class | TTL | Data |
+----------------------------------+

+----------------------------------+
|     Authority Section            |
| Name | Type | Class | TTL | Data |
+----------------------------------+

+----------------------------------+
|     Additional Section           |
| Name | Type | Class | TTL | Data |
+----------------------------------+
```

**16-bit ID Usage:**
- **Purpose**: Match query with reply
- **Length**: 16 bits = 0 to 65535 possible values
- **Assignment**: Client generates query ID randomly
- **Matching**: Server copies same ID in reply
- **Why**: If client sends multiple queries, it needs to know which reply corresponds to which query
- **Real-world**: Used when multiple DNS queries are in flight simultaneously

**Example:**
```
Query Message:
  ID: 12345
  Question: google.com (A record)?

Reply Message:
  ID: 12345 (SAME ID!)
  Answer: 64.233.187.99
```

**Our Implementation:**
```python
def resolve_iterative(domain, record_type):
    query_id = random.randint(1, 65535)  # Generate random 16-bit ID

    # Query message
    query = DNSMessage(query_id=query_id, is_query=True, ...)

    # Reply message
    reply = DNSMessage(query_id=query_id, is_query=False, ...)  # Same ID
```

---

### Q4: Explain DNS flags in the message header

**Answer:**

**Common DNS Flags:**

| Flag | Bits | Meaning | Query | Reply |
|------|------|---------|-------|-------|
| **QR** | 1 bit | Query (0) or Reply (1) | 0 | 1 |
| **Opcode** | 4 bits | Query type (standard=0) | 0 | 0 |
| **AA** | 1 bit | Authoritative Answer | 0 | 1 if authoritative |
| **TC** | 1 bit | Truncated message | 0 | 0/1 |
| **RD** | 1 bit | Recursion Desired | 1 | 1 |
| **RA** | 1 bit | Recursion Available | 0 | 1 if available |
| **RCODE** | 4 bits | Response code (0=OK) | 0 | 0-5 |

**Our Implementation:**
```python
@dataclass
class DNSMessage:
    query_id: int                    # 16-bit ID
    is_query: bool                   # QR flag (0=query, 1=reply)
    is_recursive: bool               # RD flag (recursion desired)
    is_authoritative: bool = False   # AA flag
    is_truncated: bool = False       # TC flag

# Query message (iterative):
query = DNSMessage(
    query_id=12345,
    is_query=True,              # QR=0
    is_recursive=False,         # RD=0 (iterative)
    is_authoritative=False      # AA=0
)

# Response message (authoritative):
reply = DNSMessage(
    query_id=12345,             # Same ID
    is_query=False,             # QR=1
    is_recursive=True,          # RD=1
    is_authoritative=True       # AA=1 (from authoritative server)
)
```

---

## 3. DNS Server Hierarchy

### Q5: Explain how Root → TLD → Authoritative server hierarchy works

**Answer:**

**Server Roles:**

```
ROOT DNS SERVER (13 servers worldwide)
  Role: Knows where all TLD servers are
  Stores: TLD server addresses (.com, .org, .edu, etc.)
  Does NOT store: Actual domain information
  Example: "For .com domains, ask ns1.verisign.com"

      ↓

TLD DNS SERVER (.com, .org, .edu, etc.)
  Role: Knows which authoritative server for each domain
  Stores: NS records for domains under this TLD
  Does NOT store: Actual IP addresses
  Example: "For google.com, ask ns1.google.com"

      ↓

AUTHORITATIVE DNS SERVER (maintained by domain owner)
  Role: Stores actual DNS records for the domain
  Stores: A records (IPs), MX records (mail), NS records, TXT, etc.
  Returns: Final answers to queries
  Example: "google.com resolves to 64.233.187.99"
```

**Real Example - Resolving google.com:**

```
Query: What is the IP of google.com?

Step 1: Query Root Server
  Root: "I don't know google.com, but ask TLD server for .com"
  Returns: Referral to verisign.com (TLD server)

Step 2: Query TLD Server (.com)
  TLD: "I don't know google.com, but ask Google's server"
  Returns: Referral to ns1.google.com (Authoritative)

Step 3: Query Authoritative Server
  Auth: "I have the answer! google.com = 64.233.187.99"
  Returns: Final answer (A record)
```

**Our Implementation:**
```python
# Root DNS Server
class RootDNSServer:
    def query(self, domain):  # "google.com"
        tld = ".com"  # Extract TLD
        return self.tld_servers[".com"]  # Return TLD server reference

# TLD DNS Server
class TLDServer:
    def query(self, domain, record_type):  # "google.com"
        auth_server = self.authoritative_servers["google.com"]
        return auth_server  # Return authoritative server reference

# Authoritative DNS Server
class AuthoritativeDNSServer:
    def query(self, domain, record_type):  # "google.com", "A"
        records = self.records[RecordType.A]  # Get actual records
        return records, is_authoritative  # Return final answer
```

---

### Q6: Why can't TLD server return the final IP address?

**Answer:**

**Short Answer:** TLD servers don't store final IP addresses - they're too large and impractical.

**Detailed Explanation:**

**Problem - TLD Server Responsibilities:**
- There are 250+ million registered domains under .com alone
- Each domain needs multiple A records (redundancy)
- Each domain needs MX, NS, TXT records
- Storing all this data centrally would be impractical

**Solution - Distributed DNS:**
- Root knows about TLD servers
- TLD knows about authoritative servers
- Authoritative servers store actual data
- This distribution prevents single point of failure
- Load is distributed across hierarchy

**Why This Design:**

| Hierarchy Level | Responsibility | Number of Records | Data Size |
|-----------------|-----------------|-------------------|-----------|
| **Root** | TLD referrals | ~300 (TLDs) | Small MB |
| **TLD** | Domain referrals | 250 million (for .com) | Several GB |
| **Authoritative** | Actual records | Per-domain (~10-100) | Very small |

**Scalability Advantage:**
- If Google changes their DNS records, only their server updates
- Not all TLD servers need updating
- Not all root servers need updating
- Changes propagate through TTL (Time To Live)

---

## 4. DNS Caching

### Q7: How does DNS caching work? When is CACHE HIT vs CACHE MISS?

**Answer:**

**DNS Caching Purpose:**
- Reduce latency (cached answer is immediate)
- Reduce load on DNS servers
- Improve overall performance

**CACHE HIT:**
```
Query: "What's google.com?"
Check Cache: YES, found!
Action: Return immediately
Time: ~1 microsecond (instant)
Queries Made: 0
Print: [CACHE HIT] google.com
```

**CACHE MISS:**
```
Query: "What's facebook.com?"
Check Cache: NO, not found
Action: Query DNS servers (3-4 queries)
Time: 50-200 milliseconds
Queries Made: 3-4
Print: [CACHE MISS] facebook.com
        [CACHE] Result cached for future queries
```

**Cache Storage Example:**
```python
Cache State After 3 Queries:
{
  ("google.com", RecordType.A): [
    DNSRecord("google.com", A, 300, "64.233.187.99"),
    DNSRecord("google.com", A, 300, "72.14.207.99"),
  ],
  ("facebook.com", RecordType.A): [
    DNSRecord("facebook.com", A, 300, "31.13.64.35"),
  ],
  ("github.com", RecordType.A): [
    DNSRecord("github.com", A, 300, "140.82.113.4"),
  ]
}
```

**Our Implementation:**
```python
class DNSCache:
    def put(self, domain, record_type, records):
        """Add to cache"""
        key = (domain, record_type)
        self.cache[key] = records

    def get(self, domain, record_type):
        """Retrieve from cache"""
        key = (domain, record_type)
        if key in self.cache:
            self.hits += 1
            return self.cache[key]  # HIT
        self.misses += 1
        return None  # MISS

# Usage in resolution
if self.cache.is_cached(domain, record_type):
    print("[CACHE HIT]", domain)
    return self.cache.get(domain, record_type)
else:
    print("[CACHE MISS]", domain)
    # Query DNS servers...
    self.cache.put(domain, record_type, results)
```

---

### Q8: What is LRU eviction? When and why does cache flush happen?

**Answer:**

**LRU = Least Recently Used Eviction**

**When Cache Flush Happens:**
```
Cache Limit: 5 entries
Cache Status: [Google.com, Facebook.com, GitHub.com, YouTube.com, StackOverflow.com]
              (5/5 - FULL!)

New Query: stackoverflow.dev

Action:
1. Find least recently used entry (oldest access time)
   -> GitHub.com was accessed 5 minutes ago (oldest)
2. Remove GitHub.com from cache
   Print: [CACHE FLUSH] Removed LRU entry for github.com
3. Add stackoverflow.dev to cache
4. Cache Status: [Google, Facebook, YouTube, StackOverflow, StackOverflow.dev]
               (5/5 - still full)
```

**Why LRU Policy:**
- Simple to implement
- Fair to frequently-used domains (they stay cached longer)
- Unused domains get evicted automatically
- No manual cache management needed

**Alternative Eviction Policies:**
| Policy | Implementation | Pros | Cons |
|--------|-----------------|------|------|
| **LRU** | Remove oldest accessed | Fair, simple | Requires timestamps |
| **FIFO** | Remove oldest added | Very simple | May remove active domains |
| **LFU** | Remove rarely accessed | Keeps popular | Complex |
| **TTL** | Expire after timeout | Automatic | Doesn't clear full cache |

**Our Implementation:**
```python
class DNSCache:
    def __init__(self, max_size=5):
        self.max_size = max_size
        self.cache = {}  # (domain, type) -> records
        self.access_time = {}  # (domain, type) -> timestamp

    def put(self, domain, record_type, records):
        key = (domain, record_type)

        # If cache full, remove LRU entry
        if len(self.cache) >= self.max_size and key not in self.cache:
            # Find entry with minimum access time (oldest)
            oldest_key = min(self.access_time, key=self.access_time.get)
            del self.cache[oldest_key]
            del self.access_time[oldest_key]
            print(f"[CACHE FLUSH] Removed LRU entry for {oldest_key[0]}")

        # Add new entry
        self.cache[key] = records
        self.access_time[key] = datetime.now().timestamp()
```

**Example Run:**
```
Query 1: google.com -> MISS -> CACHE: (google, 64.233.187.99)
Query 2: facebook.com -> MISS -> CACHE: (google, facebook)
Query 3: github.com -> MISS -> CACHE: (google, facebook, github)
Query 4: youtube.com -> MISS -> CACHE: (google, facebook, github, youtube)
Query 5: stackoverflow.com -> MISS -> CACHE: (google, facebook, github, youtube, stackoverflow)
Query 6: new-site.com -> MISS -> [CACHE FLUSH] Removed github.com (oldest)
                                  CACHE: (google, facebook, youtube, stackoverflow, new-site)
Query 7: google.com -> HIT (still cached!)
Query 8: github.com -> MISS (was removed!)
```

---

## 5. DNS Records

### Q9: What are A, NS, and MX records? Give real examples

**Answer:**

**A Records (Address Records)**
- **Purpose**: Maps domain name to IPv4 address
- **Format**: domain.com -> 192.0.2.1
- **Returns**: Single IPv4 address
- **Query Type**: dns_query(domain, RecordType.A)
- **TTL**: Usually 300-3600 seconds

**Example - Google:**
```
google.com A 64.233.187.99
google.com A 72.14.207.99
google.com A 64.233.167.99
```
Multiple A records = Load balancing (traffic distributed)

---

**NS Records (Nameserver Records)**
- **Purpose**: Delegates authority for a domain to nameservers
- **Format**: domain.com -> ns1.domain.com
- **Returns**: Nameserver domain names (not IPs)
- **Query Type**: dns_query(domain, RecordType.NS)
- **TTL**: Usually 172800 (48 hours)

**Example - Google:**
```
google.com NS ns1.google.com.
google.com NS ns2.google.com.
google.com NS ns3.google.com.
google.com NS ns4.google.com.
```
Multiple NS records = Redundancy (if one server down, others handle queries)

---

**MX Records (Mail Exchange Records)**
- **Purpose**: Routes email to mail servers
- **Format**: domain.com -> 10 mail.domain.com
- **Returns**: Priority + mail server address
- **Query Type**: dns_query(domain, RecordType.MX)
- **TTL**: Usually 3600 seconds

**Example - Google:**
```
google.com MX 10 smtp1.google.com.
google.com MX 10 smtp2.google.com.
google.com MX 10 smtp3.google.com.
google.com MX 10 smtp4.google.com.
```
Lower number = Higher priority (preferred mail server)

---

**Real-World Use:**

```
User sends email to user@google.com

Step 1: DNS query for google.com MX records
Result: Need to send to SMTP server with priority 10

Step 2: DNS query for smtp1.google.com A record
Result: Get SMTP server IP address

Step 3: Connect to that IP address and send email
```

**Our Implementation:**
```python
@dataclass
class DNSRecord:
    domain_name: str          # "google.com"
    record_type: RecordType   # A, NS, or MX
    ttl: int                  # 300
    data: str                 # "64.233.187.99" (A) or "ns1.google.com." (NS)
    priority: Optional[int]   # 10 for MX records, None for A/NS

# Example creation
a_record = DNSRecord(
    domain_name="google.com",
    record_type=RecordType.A,
    ttl=300,
    data="64.233.187.99",
    priority=None
)

mx_record = DNSRecord(
    domain_name="google.com",
    record_type=RecordType.MX,
    ttl=3600,
    data="smtp.google.com.",
    priority=10
)
```

---

### Q10: What "real DNS records" are used in your implementation?

**Answer:**

**Domains in Our Database:**

1. **google.com**
   ```
   A: 64.233.187.99, 72.14.207.99, 64.233.167.99
   NS: ns1.google.com., ns2.google.com., ns3.google.com., ns4.google.com.
   MX: 10 smtp1.google.com., 10 smtp2.google.com., 10 smtp3.google.com., 10 smtp4.google.com.
   ```

2. **facebook.com**
   ```
   A: 31.13.64.35, 31.13.64.36
   NS: a.ns.facebook.com., b.ns.facebook.com.
   MX: 10 aspmx.l.google.com., 20 alt1.aspmx.l.google.com.
   ```

3. **github.com**
   ```
   A: 140.82.113.4, 140.82.114.4
   NS: ns1.github.com., ns2.github.com.
   MX: 10 mail.github.com.
   ```

4. **youtube.com**
   ```
   A: 142.250.185.46, 142.251.41.14
   NS: ns1.youtube.com., ns2.youtube.com.
   MX: 10 mail.youtube.com.
   ```

5. **stackoverflow.com**
   ```
   A: 151.101.1.140, 151.101.65.140
   NS: ns1.stack.com., ns2.stack.com.
   MX: 10 mail.stackoverflow.com.
   ```

**Source:** These are actual current DNS records (or close approximations)

**Database Location in Code:**
```python
def _load_records(self):  # Line 177 in AuthoritativeDNSServer
    dns_database = {
        "google.com": {...},
        "facebook.com": {...},
        # ... etc
    }
```

---

## 6. Implementation-Specific Questions

### Q11: How do you distinguish between iterative and recursive resolution in your code?

**Answer:**

**Code Level:**
```python
# Iterative Resolution
records, log = local_server.resolve_iterative("google.com", RecordType.A)

# Recursive Resolution
records, log = local_server.resolve_recursive("facebook.com", RecordType.A)
```

**Flag Level:**
```python
# Query for iterative
query_iterative = DNSMessage(
    is_query=True,
    is_recursive=False  # NOT recursive
)

# Query for recursive
query_recursive = DNSMessage(
    is_query=True,
    is_recursive=True  # IS recursive
)
```

**Process Level:**

**Iterative (Multiple queries):**
```
resolve_iterative():
    1. Check cache
    2. Query Root Server    <- Client does this
    3. Query TLD Server     <- Client does this
    4. Query Auth Server    <- Client does this
    5. Cache result
    return results
```

**Recursive (Single query to server):**
```
resolve_recursive():
    1. Check cache
    2. Send query to root (marked as recursive)
    3. [Inside LocalServer]
       - Query TLD
       - Query Auth
    4. Receive final answer from server
    5. Cache result
    return results
```

---

### Q12: Walk me through a complete resolution example (google.com)

**Answer:**

**Example: First Query for google.com (Iterative)**

```
Step 1: Client asks local server for google.com
   Query: resolve_iterative("google.com", RecordType.A)

Step 2: Local server checks cache
   Cache.is_cached("google.com", A)?
   Result: NO -> CACHE MISS

Step 3: Create query message
   query_id = 12345 (random 16-bit number)
   DNSMessage(
       query_id=12345,
       is_query=True,
       is_recursive=False,
       questions=[DNSQuestion("google.com", A)]
   )

Step 4: Query ROOT DNS Server
   root_server.query("google.com")
   Root extracts TLD: ".com"
   Root returns: TLD server for .com

Step 5: Query TLD DNS Server for .com
   tld_server.query("google.com", A)
   TLD checks: Do I have "google.com"?
   Yes! Return authoritative server: google.com's nameserver
   Also return NS records as referral

Step 6: Query AUTHORITATIVE DNS Server
   auth_server.query("google.com", A)
   Auth: "This is my domain, I have the records"
   Return: [
       A record: 64.233.187.99,
       A record: 72.14.207.99,
       A record: 64.233.167.99
   ]

Step 7: Client receives answer
   Store in cache
   Display results:
   google.com/64.233.187.99
   -- DNS INFORMATION --
   A: 64.233.187.99, 72.14.207.99, 64.233.167.99
   NS: ns1.google.com., ns2.google.com., ns3.google.com., ns4.google.com.
   MX: 10 smtp1.google.com., ...

Step 8: Second query for google.com (IMMEDIATE)
   Query: resolve_iterative("google.com", RecordType.A)
   Cache.is_cached("google.com", A)?
   Result: YES -> CACHE HIT
   Return cached result immediately (no server queries!)
```

**Output Shown:**
```
======================================================================
[QUERY] ITERATIVE RESOLUTION: google.com (A)
======================================================================
[ERROR] CACHE MISS for google.com

[STEP 1] Query ROOT DNS Server for google.com
  [OK] Root Server: 'Query TLD server for google.com'

[STEP 2] Query TLD DNS Server for google.com
  [OK] TLD Server: 'Query Authoritative server google.com'
    NS Record: ns4.google.com.
    ...

[STEP 3] Query AUTHORITATIVE DNS Server for google.com
  [OK] Authoritative Server found 3 records:
    A: 64.233.187.99
    A: 72.14.207.99
    A: 64.233.167.99

  [CACHE] Result cached for future queries

----------------------------------------------------------------------
 FINAL RESULT:
----------------------------------------------------------------------
google.com/64.233.187.99
-- DNS INFORMATION --
A: 64.233.187.99, 72.14.207.99, 64.233.167.99
NS: ns4.google.com., ns1.google.com., ns2.google.com., ns3.google.com.
MX: 10 smtp4.google.com., 10 smtp1.google.com., 10 smtp2.google.com., 10 smtp3.google.com.
```

---

## 7. Theoretical Questions (Concepty-based)

### Q13: Why do we need DNS at all? Why not just memorize IP addresses?

**Answer:**

**Problems with Just IP Addresses:**

1. **IPs are Hard to Remember**
   - google.com = 64.233.187.99 ✗ (hard to remember)
   - google.com ✓ (easy to remember)

2. **Servers Change IPs Frequently**
   - Website might move to new server
   - Google might want to change IPs
   - Users don't need to know about changes
   - With DNS, just update DNS record

3. **Load Balancing**
   - google.com can have 3 IPs
   - Traffic distributed across 3 servers
   - If you hardcoded IP, you'd miss benefits

4. **Business Changes**
   - Companies merge/restructure
   - Need to redirect traffic without telling users
   - DNS allows instant redirects

5. **Geographic Distribution**
   - Different countries get different IPs
   - User in Pakistan -> Pakistan server IP
   - User in USA -> USA server IP
   - Same domain name, different IPs!

**Analogy:**
- IP address = Physical address (123 Main St, House 45)
- Domain name = Phone book number (Google: 411)
- DNS = Phone book (maps number to address)

---

### Q14: Why is DNS hierarchical? Why not centralize everything at one server?

**Answer:**

**Centralized Problem (Single Server):**
```
All users worldwide -> ONE server
All DNS queries -> ONE server
Problem:
- That server crashes = ENTIRE INTERNET DOWN
- Can't handle billions of queries/second
- More queries = server slower
```

**Hierarchical Solution (Root -> TLD -> Authoritative):**
```
13 Root Servers worldwide handle: "Which TLD?"
500+ TLD Servers handle: "Which authoritative?"
Millions of Authoritative Servers handle: "Here's the answer"

Benefits:
- If one Root fails, 12 others still work
- TLD servers handle domain delegation
- Authoritative servers handle specific domain
- Queries spread across much more infrastructure
```

**Scalability Math:**

| Approach | Servers | Queries Handled | Failure Impact |
|----------|---------|-----------------|-----------------|
| **Centralized** | 1 | 1 million/sec | 100% outage |
| **Root level** | 13 | ? | 7.7% impact |
| **TLD level** | 500+ | ? | < 1% impact |
| **Authoritative** | Millions | Scalable | 0% impact |

---

### Q15: How does TTL (Time-To-Live) relate to caching?

**Answer:**

**TTL = Time-To-Live**
- **Unit**: Seconds
- **Meaning**: How long a DNS record is valid
- **Example**: TTL = 300 means record is good for 5 minutes

**TTL in Resolution:**
```
Step 1: Query "google.com"
Step 2: Receive: 64.233.187.99 (TTL: 300)
Step 3: Cache for 300 seconds
Step 4: After 300 seconds, record expires
Step 5: New query needed (if requested after expiry)
```

**Trade-offs:**

| TTL | Pros | Cons |
|-----|------|------|
| **Low (60s)** | Fast updates | More queries, more server load |
| **High (86400s)** | Less queries | Slow to reflect changes |
| **Medium (3600s)** | Balance | Most common |

**Real Examples:**
```
google.com:     3600 (1 hour)  - changes rarely
twitter.com:    300 (5 min)    - changes frequently
yoursite.com:   300 (5 min)    - if updating often
```

**Our Implementation Note:**
- We set TTL = 300 for all records
- We don't implement time-based expiration
- Cache stays until LRU eviction
- In real DNS: would expire after TTL seconds

---

## 8. Challenge Questions

### Q16: What if someone queries for a domain not in your database?

**Answer:**

**Scenario:**
```
Query: unknown-domain.com

Execution Flow:
1. Root server: "What TLD?" -> ".com"
2. TLD server: "What authoritative?" -> Not found!
3. Return: No records found
4. Print: "No records found for unknown-domain.com"
```

**Code Handling:**
```python
def query(self, domain, record_type):
    if domain in self.authoritative_servers:
        auth_server = self.authoritative_servers[domain]
        # Found!
    return auth_server, ns_records  # Returns None if not found

if not auth_server:
    print(f"- [ERROR] Not found at TLD level")
    return [], step_log  # Empty list = no records
```

**Real-world:** Would return NXDOMAIN error

---

### Q17: What if you wanted to add a new domain? How would you do it?

**Answer:**

**Steps:**

```python
# 1. Create authoritative server for new domain
auth_reddit = AuthoritativeDNSServer("reddit.com")

# 2. Register with TLD server
tld_com.register_domain("reddit.com", auth_reddit)

# Now it's available for queries!
records = client.resolve_iterative("reddit.com", RecordType.A)
```

**Adding Custom Records:**

Edit `_load_records()` in AuthoritativeDNSServer:

```python
def _load_records(self):
    dns_database = {
        "google.com": {...},
        "reddit.com": {  # NEW
            RecordType.A: [
                ("151.101.1.140", None),
                ("151.101.65.140", None),
            ],
            RecordType.NS: [
                ("ns1.reddit.com.", None),
                ("ns2.reddit.com.", None),
            ],
            RecordType.MX: [
                ("mail.reddit.com.", 10),
            ]
        }
    }
```

---

## 9. Viva Demo Flow (5 minute explanation)

### Q18: Walk me through a 5-minute demo explanation

**Answer:**

**Minute 1: Introduction (0:00-1:00)**
```
"This is a DNS simulation showing how domain names resolve to IP addresses.
The program has 3 DNS servers: Root, TLD, and Authoritative.
It demonstrates both Iterative and Recursive resolution.
First query misses cache, second query hits cache showing how caching helps."
```

**Minute 2: Iterative Resolution (1:00-2:00)**
```
"Let me show iterative resolution first. The client queries:
Step 1: Root server -> gives TLD referral
Step 2: TLD server -> gives Authoritative referral
Step 3: Authoritative server -> gives final IP address
Three queries total. You can see each step printed clearly.
The 16-bit ID (like 12345) connects query and reply."
```

**Minute 3: Recursive Resolution (2:00-3:00)**
```
"Now recursive resolution. Client makes ONE query to local server.
Local server does all the work: queries Root, TLD, and Authoritative.
Local server returns final answer to client.
The difference: Iterative = client does work, Recursive = server does work."
```

**Minute 4: Caching (3:00-4:00)**
```
"When we query google.com second time, it's a Cache HIT.
Result returns immediately without any server queries.
When cache fills up (5 entries), it evicts the least recently used entry.
This shows how caching reduces server load and improves performance."
```

**Minute 5: DNS Records (4:00-5:00)**
```
"Here are the actual DNS records - A records (IP addresses),
NS records (nameserver delegation), and MX records (email servers).
These are real records I hard-coded in the database.
The program clearly shows the format required by the assignment."
```

---

## 10. Sample Viva Questions That Might Be Asked

### Expected Questions from Instructor:

1. ✓ "What's the difference between iterative and recursive?"
2. ✓ "How does caching work?"
3. ✓ "Why is DNS hierarchical?"
4. ✓ "What does the 16-bit ID represent?"
5. ✓ "Show me the DNS message format"
6. ✓ "Explain the A, NS, MX records"
7. ✓ "What happens with cache overflow?"
8. ✓ "Can you add a new domain?"
9. ✓ "Why not use a single DNS server?"
10. ✓ "What's the output format?"

---

## Quick Reference Answers

| Topic | Key Point |
|-------|-----------|
| **Iterative** | Multiple queries by client, each to different server |
| **Recursive** | Single query to local server, server does internal work |
| **16-bit ID** | Matches query with reply |
| **Cache HIT** | Found in cache, return immediately |
| **Cache MISS** | Not in cache, query servers |
| **LRU Eviction** | Remove oldest accessed entry when cache full |
| **Root Server** | Returns TLD referral |
| **TLD Server** | Returns Authoritative referral |
| **Authoritative** | Returns final answer (IP address) |
| **A Record** | IPv4 address |
| **NS Record** | Nameserver (delegation) |
| **MX Record** | Mail server with priority |

---

## Final Tips for Viva

✓ **Prepare:** Know the flow diagram by heart
✓ **Practice:** Run the program 10 times
✓ **Understand:** Don't just memorize - understand WHY
✓ **Draw:** Be ready to draw hierarchy and flow diagrams
✓ **Explain:** Clear, step-by-step explanations
✓ **Code:** Know where key logic is (line numbers)
✓ **Examples:** Use real domains (google.com, facebook.com)
✓ **Time:** Speak slowly, take 5 minutes for demo
✓ **Questions:** Listen carefully, answer directly
✓ **Confidence:** Show you built this yourself
