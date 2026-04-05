# DNS Implementation - Code Architecture & Explanation

## Project Overview

This DNS simulation application demonstrates how Domain Name System (DNS) resolution works internally when a client resolves a domain name that is not cached locally. It implements a complete DNS hierarchical structure with Root, TLD, and Authoritative servers, complete with local caching and both iterative and recursive resolution mechanisms.

---

## Architecture Overview

### System Components

```

+------------------+
| DNS Client       |
+--------+---------+
         |
         | Query
         |
+--------v---------+
| Local DNS Server | (with Cache)
+--------+---------+
         |
         +------- Root DNS Server
              |
              +---- TLD Server (.com)
                   |
                   +---- Authoritative Server (google.com)
```

---

## Core Classes & Components

### 1. **DNSMessage** (lines 43-89)
**Purpose:** Implements DNS protocol message format per RFC 1035

**Key Attributes:**
- `query_id`: 16-bit identification (same in query & reply)
- `is_query`: Boolean flag (True = query, False = reply)
- `is_recursive`: Recursion desired flag
- `is_authoritative`: Authoritative answer flag
- `questions`: List of DNS questions
- `answers`: List of answer resource records
- `authority`: Authority resource records
- `additional`: Additional information records

**Key Method:**
- `__str__()`: Formats message for display showing all fields

---

### 2. **DNSRecord** (lines 30-36)
**Purpose:** Represents a DNS Resource Record (RR)

**Fields:**
- `domain_name`: Domain being queried (e.g., "google.com")
- `record_type`: Type of record (A, NS, MX, CNAME)
- `ttl`: Time-to-live in seconds
- `data`: The actual data (IP address, nameserver, etc.)
- `priority`: Priority value (used for MX records)

**Example:**
```python
DNSRecord(
    domain_name="google.com",
    record_type=RecordType.A,
    ttl=300,
    data="64.233.187.99",
    priority=None
)
```

---

### 3. **DNSCache** (lines 92-154)
**Purpose:** Local DNS cache with LRU (Least Recently Used) eviction policy

**Key Methods:**
- `put(domain, record_type, records)`: Add records to cache
  - If cache is full, removes LRU entry
  - Updates access timestamp

- `get(domain, record_type)`: Retrieve from cache
  - Returns None if not found (CACHE MISS)
  - Updates access time on HIT

- `is_cached()`: Check if entry exists
- `stats()`: Returns cache hit/miss statistics

**Cache Features:**
- **Max Size**: Configurable (default 5)
- **Eviction**: Removes oldest accessed entry when full
- **Tracking**: Records hits and misses for statistics

---

### 4. **AuthoritativeDNSServer** (lines 157-265)
**Purpose:** Stores actual DNS records for a domain

**Key Methods:**
- `_load_records()`: Loads hard-coded DNS database
  - Stores real Google, Facebook, GitHub DNS records
  - Records include A, NS, MX types

- `query(domain, record_type)`: Returns records if authoritative
  - Returns (records, is_authoritative) tuple
  - Only responds if domain matches

**DNS Database Example:**
```
google.com:
  A Records: 64.233.187.99, 72.14.207.99, 64.233.167.99
  NS Records: ns1-4.google.com
  MX Records: smtp1-4.google.com (priority 10)
```

---

### 5. **TLDServer** (lines 268-296)
**Purpose:** Top-Level Domain (TLD) server (.com, .org, etc.)

**Key Methods:**
- `register_domain()`: Maps domain to its authoritative server
- `query()`: Returns referral to authoritative server
  - Returns NS records pointing to authoritative server
  - Does NOT return final IP addresses

**Role in Resolution:**
```
Client -> TLD -> "Query authoritative server X for this domain"
```

---

### 6. **RootDNSServer** (lines 299-320)
**Purpose:** Root DNS server (highest level)

**Key Methods:**
- `register_tld()`: Maps TLD to TLD server
- `query()`: Returns referral to TLD server
  - Extracts TLD from domain (google.com -> .com)
  - Returns TLD server reference

**Role in Resolution:**
```
Client -> Root -> "Query TLD server for .com domain"
```

---

### 7. **LocalDNSServer** (lines 323-476)
**Purpose:** Client's local DNS resolver with caching

**Key Methods:**

#### `resolve_iterative(domain, record_type)` (lines 352-405)
**Iterative Resolution Steps:**

1. **Check Cache**: Return if cached
2. **Query Root**: "Which TLD server?"
3. **Query TLD**: "Which authoritative server?"
4. **Query Auth**: "Give me the IP address"
5. **Cache Result**: Store for future use

**Output:**
```
[STEP 1] Query ROOT DNS Server
[STEP 2] Query TLD DNS Server
[STEP 3] Query AUTHORITATIVE DNS Server
Result cached
```

**Characteristics:**
- Client makes multiple queries
- Client controls the flow
- Server returns referrals, not answers

---

#### `resolve_recursive(domain, record_type)` (lines 408-476)
**Recursive Resolution Steps:**

1. **Check Cache**: Return if cached
2. **Send Query to Root**: One recursive query
3. **Root queries TLD** (on behalf of client)
4. **TLD queries Auth** (on behalf of client)
5. **Receive Final Answer**: Only one reply to client

**Output:**
```
[SEND] Client sends recursive query
[LOCAL RESOLVER] Processing...
  [-> ROOT] ...
  [-> TLD] ...
  [-> AUTH] ...
[RECEIVE] Server sends reply with answer
```

**Characteristics:**
- Client makes single query
- Server handles all lookups
- Server returns final answer

---

### 8. **DNSClient** (lines 479-493)
**Purpose:** Simple interface for DNS queries

**Key Methods:**
- `resolve_recursive()`: Performs recursive resolution
- `resolve_iterative()`: Performs iterative resolution

---

## DNS Resolution Flow

### Iterative Resolution Example: google.com

```
CLIENT                ROOT             TLD              AUTHORITATIVE
  |                    |               |                    |
  +--Query google----->|               |                    |
  |                    |               |                    |
  |<--Redirect to TLD--+               |                    |
  |                                     |                    |
  +--Query google----->|               |                    |
  |                    |               |                    |
  |<----Redirect to Auth----------------+                    |
  |                                                          |
  +--Query google----->|              |                    |
  |                                     |                    |
  |<-----Answer: 64.233.187.99----------+                    |
```

### Recursive Resolution Example: facebook.com

```
CLIENT              LOCAL            ROOT            TLD          AUTHORITATIVE
  |               RESOLVER             |              |               |
  +--Query----->|                       |              |               |
  |             | Query Root----------->|              |               |
  |             |<------Referral--------+              |               |
  |             |                                       |               |
  |             | Query TLD---------->|               |               |
  |             |<-----Referral--------+               |               |
  |             |                                       |               |
  |             | Query Auth------->|              |               |
  |             |<--------Answer-----+               |               |
  |             |                                       |               |
  |<---Answer---|                                       |               |
```

---

## Cache Management

### Cache Operations

**1. Cache HIT:**
```
Query: google.com
Found in cache?
-> YES: Return immediately (no server queries)
-> Print: [CACHE HIT] google.com
```

**2. Cache MISS:**
```
Query: facebook.com
Found in cache?
-> NO: Query DNS servers
-> After resolution, store result
-> Print: [CACHE MISS] facebook.com
       [CACHE] Result cached for future queries
```

**3. Cache Eviction (LRU):**
```
Cache Status: 5/5 entries (FULL)
New query arrives for youtube.com
-> Find least recently used entry
-> Remove it
-> Print: [CACHE FLUSH] Removed LRU entry for github.com
-> Add new entry
```

---

## DNS Message Format

### Query Message Structure

```
[16 bits] Query ID: 12345
[16 bits] Flags: [Query, No Recursion, ...]
[Variable] Questions: {google.com, Type: A}
[0 entries] Answers: (empty in query)
```

### Reply Message Structure

```
[16 bits] Query ID: 12345 (same as query)
[16 bits] Flags: [Reply, Authoritative, ...]
[Variable] Questions: {google.com, Type: A}
[Variable] Answers: {64.233.187.99}
[Variable] Authority: {ns1.google.com}
[Variable] Additional: (if provided)
```

---

## Real DNS Records Used

### Google.com
```
A: 64.233.187.99, 72.14.207.99, 64.233.167.99
NS: ns1.google.com., ns2.google.com., ns3.google.com., ns4.google.com.
MX: 10 smtp1.google.com., 10 smtp2.google.com., 10 smtp3.google.com., 10 smtp4.google.com.
```

### Facebook.com
```
A: 31.13.64.35, 31.13.64.36
NS: a.ns.facebook.com., b.ns.facebook.com.
MX: 10 aspmx.l.google.com., 20 alt1.aspmx.l.google.com.
```

### GitHub.com
```
A: 140.82.113.4, 140.82.114.4
NS: ns1.github.com., ns2.github.com.
MX: 10 mail.github.com.
```

### YouTube.com
```
A: 142.250.185.46, 142.251.41.14
NS: ns1.youtube.com., ns2.youtube.com.
MX: 10 mail.youtube.com.
```

### StackOverflow.com
```
A: 151.101.1.140, 151.101.65.140
NS: ns1.stack.com., ns2.stack.com.
MX: 10 mail.stackoverflow.com.
```

---

## Key Features Implemented

| Feature | Implementation |
|---------|-----------------|
| **16-bit Query ID** | Used in DNSMessage.query_id |
| **Iterative Resolution** | resolve_iterative() method |
| **Recursive Resolution** | resolve_recursive() method |
| **DNS Caching** | DNSCache class with LRU eviction |
| **Cache Status** | CACHE HIT/MISS messages |
| **Auto-Flushing** | LRU removal when cache full |
| **Real DNS Records** | Hard-coded in AuthoritativeDNSServer |
| **A, NS, MX Records** | RecordType enum + storage |
| **Hierarchical Servers** | Root -> TLD -> Authoritative |
| **Message Logging** | Detailed step-by-step output |

---

## Output Format

### Iterative Resolution Output
```
======================================================================
[QUERY] ITERATIVE RESOLUTION: google.com (A)
======================================================================
[ERROR] CACHE MISS for google.com

[STEP 1] Query ROOT DNS Server for google.com
  [OK] Root Server: 'Query TLD server for google.com'

[STEP 2] Query TLD DNS Server for google.com
  [OK] TLD Server: 'Query Authoritative server google.com'

[STEP 3] Query AUTHORITATIVE DNS Server for google.com
  [OK] Authoritative Server found 3 records:

 FINAL RESULT:
----------------------------------------------------------------------
google.com/64.233.187.99
-- DNS INFORMATION --
A: 64.233.187.99, 72.14.207.99, 64.233.167.99
NS: ns4.google.com., ns1.google.com., ns2.google.com., ns3.google.com.
MX: 10 smtp4.google.com., 10 smtp1.google.com., 10 smtp2.google.com., 10 smtp3.google.com.
```

### Recursive Resolution Output
```
======================================================================
[RECURSIVE] RECURSIVE RESOLUTION: facebook.com (A)
======================================================================
[ERROR] CACHE MISS for facebook.com

[SEND] Client sends recursive query to root server:

--- DNS MESSAGE (ID: 39041) [QUERY] [Recursive: True, ...] ---

[LOCAL RESOLVER] Processing recursive query...
  [-> ROOT SERVER] Querying for facebook.com
  [-> TLD SERVER] Querying for facebook.com
  [-> AUTHORITATIVE SERVER] Querying for facebook.com

[RECEIVE] Server sends recursive reply to client:

--- DNS MESSAGE (ID: 39041) [REPLY] [Recursive: True, Authoritative: True] ---
```

---

## Code Statistics

- **Total Lines**: ~650
- **Classes**: 8
- **Enums**: 1 (RecordType)
- **Data Classes**: 3 (DNSQuestion, DNSRecord, DNSMessage)
- **Methods**: 25+
- **Test Cases**: 4

---

## Design Patterns Used

1. **Facade Pattern**: LocalDNSServer provides simple interface to complex DNS hierarchy
2. **Strategy Pattern**: Different resolution methods (iterative vs recursive)
3. **Composition Pattern**: LocalDNSServer contains RootDNSServer, TLDServer, cache
4. **Factory Pattern**: AuthoritativeDNSServer creates DNS records
5. **Observer Pattern**: Cache tracks hits/misses

---

## Extensions & Modifications

To add more features:

### Add More Domains
Edit `_load_records()` in AuthoritativeDNSServer:
```python
dns_database = {
    "example.com": {
        RecordType.A: [("93.184.216.34", None), ...],
        ...
    }
}
```

### Change Cache Size
```python
local_server = LocalDNSServer("dns.poly.edu", cache_size=10)
```

### Implement Different Eviction Policy
Modify DNSCache.put() method to use FIFO or other policy:
```python
# FIFO: def put(self, ...):
#     if len > max and not exists:
#         oldest_key = list(self.cache.keys())[0]
#         del self.cache[oldest_key]
```

### Add TTL Expiration
Implement time-based cache expiration:
```python
def is_expired(self, key):
    current_time = time.time()
    entry_time = self.access_time[key]
    ttl = self.cache[key][0].ttl
    return (current_time - entry_time) > ttl
```

---

## File Structure

```
d:\Sem 6\CN\A2\
├── dns_simulation.py          (Main implementation)
├── CODE_EXPLANATION.md         (This file - Architecture)
├── VIVA_QUESTIONS.md          (Q&A for examination)
├── DEMO_GUIDE.md              (How to run & explain)
└── SAMPLE_OUTPUT.txt          (Expected output)
```

---

## Conclusion

This DNS implementation demonstrates:
- **Hierarchical DNS architecture** (Root -> TLD -> Authoritative)
- **Query/Reply message format** with 16-bit IDs
- **Two resolution methods** (Iterative & Recursive)
- **Local caching mechanism** with LRU eviction
- **Real DNS records** for actual domains
- **Clean, object-oriented design** suitable for demonstration

The code is production-style but simplified for educational purposes.
