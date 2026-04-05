from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random


# Supported DNS record types
class RecordType(Enum):
    A = "A"
    NS = "NS"
    MX = "MX"
    CNAME = "CNAME"


@dataclass
class DNSQuestion:
    domain_name: str
    record_type: RecordType


@dataclass
class DNSRecord:
    domain_name: str
    record_type: RecordType
    ttl: int
    data: str
    priority: Optional[int] = None


@dataclass
class DNSMessage:
    query_id: int
    is_query: bool
    is_recursive: bool
    is_authoritative: bool = False
    is_truncated: bool = False
    questions: List[DNSQuestion] = field(default_factory=list)
    answers: List[DNSRecord] = field(default_factory=list)
    authority: List[DNSRecord] = field(default_factory=list)
    additional: List[DNSRecord] = field(default_factory=list)

    def __str__(self):
        direction = "QUERY" if self.is_query else "REPLY"
        flags = f"[Recursive: {self.is_recursive}, Authoritative: {self.is_authoritative}]"
        msg = f"\n--- DNS MESSAGE (ID: {self.query_id:05d}) [{direction}] {flags} ---\n"
        if self.questions:
            msg += f"QUESTIONS ({len(self.questions)}):\n"
            for q in self.questions:
                msg += f"   {q.domain_name} ({q.record_type.value})\n"
        if self.answers:
            msg += f"ANSWERS ({len(self.answers)}):\n"
            for ans in self.answers:
                if ans.priority:
                    msg += f"   {ans.domain_name} {ans.record_type.value} {ans.priority} {ans.data}\n"
                else:
                    msg += f"   {ans.domain_name} {ans.record_type.value} {ans.data}\n"
        if self.authority:
            msg += f"AUTHORITY ({len(self.authority)}):\n"
            for auth in self.authority:
                msg += f"   {auth.domain_name} {auth.record_type.value} {auth.data}\n"
        if self.additional:
            msg += f"ADDITIONAL ({len(self.additional)}):\n"
            for add in self.additional:
                msg += f"   {add.domain_name} {add.record_type.value} {add.data}\n"
        return msg


class DNSCache:
    # Simple LRU cache with hit/miss tracking
    def __init__(self, max_size=5):
        self.max_size = max_size
        self.cache: Dict[Tuple[str, RecordType], List[DNSRecord]] = {}
        self.access_time: Dict[Tuple[str, RecordType], float] = {}
        self.hits = 0
        self.misses = 0

    def put(self, domain, record_type, records):
        key = (domain, record_type)
        # Evict least recently used entry if cache is full
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = min(self.access_time, key=self.access_time.get)
            del self.cache[oldest_key]
            del self.access_time[oldest_key]
            print(f"    CACHE FLUSH: Removed LRU entry for {oldest_key[0]}")
        self.cache[key] = records
        self.access_time[key] = datetime.now().timestamp()

    def get(self, domain, record_type):
        key = (domain, record_type)
        if key in self.cache:
            self.access_time[key] = datetime.now().timestamp()
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None

    def is_cached(self, domain, record_type):
        return (domain, record_type) in self.cache

    def flush(self):
        self.cache.clear()
        self.access_time.clear()


class AuthoritativeDNSServer:
    def __init__(self, domain):
        self.domain = domain
        self.records: Dict[RecordType, List[DNSRecord]] = {
            RecordType.A: [],
            RecordType.NS: [],
            RecordType.MX: [],
            RecordType.CNAME: []
        }
        self._load_records()

    def _load_records(self):
        # Static DNS records database
        dns_database = {
            "google.com": {
                RecordType.A: [
                    ("64.233.187.99", None),
                    ("72.14.207.99", None),
                    ("64.233.167.99", None),
                ],
                RecordType.NS: [
                    ("ns4.google.com.", None),
                    ("ns1.google.com.", None),
                    ("ns2.google.com.", None),
                    ("ns3.google.com.", None),
                ],
                RecordType.MX: [
                    ("smtp4.google.com.", 10),
                    ("smtp1.google.com.", 10),
                    ("smtp2.google.com.", 10),
                    ("smtp3.google.com.", 10),
                ]
            },
            "facebook.com": {
                RecordType.A: [
                    ("31.13.64.35", None),
                    ("31.13.64.36", None),
                ],
                RecordType.NS: [
                    ("a.ns.facebook.com.", None),
                    ("b.ns.facebook.com.", None),
                ],
                RecordType.MX: [
                    ("aspmx.l.google.com.", 10),
                    ("alt1.aspmx.l.google.com.", 20),
                ]
            },
            "github.com": {
                RecordType.A: [
                    ("140.82.113.4", None),
                    ("140.82.114.4", None),
                ],
                RecordType.NS: [
                    ("ns1.github.com.", None),
                    ("ns2.github.com.", None),
                ],
                RecordType.MX: [
                    ("mail.github.com.", 10),
                ]
            },
            "youtube.com": {
                RecordType.A: [
                    ("142.250.185.46", None),
                    ("142.251.41.14", None),
                ],
                RecordType.NS: [
                    ("ns1.youtube.com.", None),
                    ("ns2.youtube.com.", None),
                ],
                RecordType.MX: [
                    ("mail.youtube.com.", 10),
                ]
            },
            "stackoverflow.com": {
                RecordType.A: [
                    ("151.101.1.140", None),
                    ("151.101.65.140", None),
                ],
                RecordType.NS: [
                    ("ns1.stack.com.", None),
                    ("ns2.stack.com.", None),
                ],
                RecordType.MX: [
                    ("mail.stackoverflow.com.", 10),
                ]
            }
        }
        if self.domain in dns_database:
            db = dns_database[self.domain]
            for record_type, records in db.items():
                for data, priority in records:
                    record = DNSRecord(
                        domain_name=self.domain,
                        record_type=record_type,
                        ttl=300,
                        data=data,
                        priority=priority
                    )
                    self.records[record_type].append(record)

    def query(self, domain, record_type):
        is_authoritative = (domain == self.domain)
        if is_authoritative:
            return self.records.get(record_type, []), True
        return [], False

    def has_domain(self, domain):
        return domain == self.domain


class TLDServer:
    def __init__(self, tld):
        self.tld = tld
        self.authoritative_servers: Dict[str, AuthoritativeDNSServer] = {}

    def register_domain(self, domain, auth_server):
        self.authoritative_servers[domain] = auth_server

    def query(self, domain, record_type):
        if domain in self.authoritative_servers:
            auth_server = self.authoritative_servers[domain]
            ns_records = auth_server.records.get(RecordType.NS, [])
            return auth_server, ns_records
        return None, []


class RootDNSServer:
    def __init__(self):
        self.tld_servers: Dict[str, TLDServer] = {}

    def register_tld(self, tld, tld_server):
        self.tld_servers[tld] = tld_server

    def query(self, domain):
        tld = "." + domain.split(".")[-1]
        if tld in self.tld_servers:
            tld_server = self.tld_servers[tld]
            return tld_server, []
        return None, []


class LocalDNSServer:
    def __init__(self, name="Local Resolver", cache_size=5):
        self.name = name
        self.cache = DNSCache(max_size=cache_size)
        self.root_server: Optional[RootDNSServer] = None
        self.query_counter = 0

    def set_root_server(self, root_server):
        self.root_server = root_server

    def resolve_iterative(self, domain, record_type=RecordType.A):
        self.query_counter += 1
        query_id = random.randint(1, 65535)
        step_log = []

        print(f"[QUERY] ITERATIVE RESOLUTION: {domain} ({record_type.value})\n")

        # Return from cache if available
        if self.cache.is_cached(domain, record_type):
            print(f"CACHE HIT for {domain}")
            return self.cache.get(domain, record_type), step_log

        print(f"CACHE MISS for {domain}")

        print(f"\n[STEP 1] Query ROOT DNS Server for {domain}")
        tld_server, _ = self.root_server.query(domain)

        if not tld_server:
            print(f"Root server has no information for {domain}")
            return [], step_log

        print(f"Root Server: 'Query TLD server for {domain}'")
        step_log.append(f"Root -> TLD Server referral")

        print(f"\n[STEP 2] Query TLD DNS Server for {domain}")
        auth_server, ns_records = tld_server.query(domain, record_type)

        if not auth_server:
            print(f"TLD server has no information for {domain}")
            return [], step_log

        print(f"TLD Server: 'Query Authoritative server {auth_server.domain}'")
        if ns_records:
            for ns in ns_records:
                print(f"    NS Record: {ns.data}")
        step_log.append(f"TLD -> Authoritative Server referral")

        print(f"\n[STEP 3] Query AUTHORITATIVE DNS Server for {domain}")
        records, is_auth = auth_server.query(domain, record_type)

        if records:
            print(f"Authoritative Server found {len(records)} records:")
            for record in records:
                if record.priority:
                    print(f"    {record.record_type.value}: {record.priority} {record.data}")
                else:
                    print(f"    {record.record_type.value}: {record.data}")
        else:
            print(f"No records found")
            return [], step_log

        self.cache.put(domain, record_type, records)
        print(f"\nResult cached for future queries")
        return records, step_log

    def resolve_recursive(self, domain, record_type=RecordType.A):
        self.query_counter += 1
        query_id = random.randint(1, 65535)
        step_log = []

        print(f"[RECURSIVE] RECURSIVE RESOLUTION: {domain} ({record_type.value})")

        # Return from cache if available
        if self.cache.is_cached(domain, record_type):
            print(f"CACHE HIT for {domain}")
            return self.cache.get(domain, record_type), step_log

        print(f"CACHE MISS for {domain}")

        query = DNSMessage(
            query_id=query_id,
            is_query=True,
            is_recursive=True,
            questions=[DNSQuestion(domain, record_type)]
        )

        print(f"\nClient sends recursive query to root server:")
        print(query)
        print("[LOCAL RESOLVER] Processing recursive query...")

        print(f"\n  [-> ROOT SERVER] Querying for {domain}")
        tld_server, _ = self.root_server.query(domain)

        if not tld_server:
            print(f" Not found at root level")
            return [], step_log

        print(f"Root: Referral to TLD server")
        step_log.append("Root Server -> TLD referral")

        print(f"\n  [-> TLD SERVER] Querying for {domain}")
        auth_server, ns_records = tld_server.query(domain, record_type)

        if not auth_server:
            print(f"Not found at TLD level")
            return [], step_log

        print(f"TLD: Referral to Authoritative server")
        step_log.append("TLD Server -> Authoritative referral")

        print(f"\n  [-> AUTHORITATIVE SERVER] Querying for {domain}")
        records, is_auth = auth_server.query(domain, record_type)

        if records:
            print(f"Found {len(records)} records")
            for record in records:
                if record.priority:
                    print(f"      {record.record_type.value}: {record.priority} {record.data}")
                else:
                    print(f"      {record.record_type.value}: {record.data}")
        else:
            print(f"    [ERROR] No records found")
            return [], step_log

        step_log.append("Authoritative Server -> Answer")

        reply = DNSMessage(
            query_id=query_id,
            is_query=False,
            is_recursive=True,
            is_authoritative=True,
            answers=records
        )

        print(f"\nServer sends recursive reply to client:")
        print(reply)
        self.cache.put(domain, record_type, records)
        print(f"\nResult cached for future queries")
        return records, step_log


class DNSClient:
    def __init__(self, local_server):
        self.local_server = local_server

    def resolve_recursive(self, domain, record_type=RecordType.A):
        return self.local_server.resolve_recursive(domain, record_type)[0]

    def resolve_iterative(self, domain, record_type=RecordType.A):
        return self.local_server.resolve_iterative(domain, record_type)[0]


def print_dns_records(domain, records):
    if not records:
        return f"No records found for {domain}\n"

    a_records = [r for r in records if r.record_type == RecordType.A]
    first_ip = a_records[0].data if a_records else "Unknown"
    output = f"{domain}/{first_ip}\n"
    output += "-- DNS INFORMATION --\n"

    a_recs = [r for r in records if r.record_type == RecordType.A]
    if a_recs:
        ips = ", ".join([r.data for r in a_recs])
        output += f"A: {ips}\n"

    ns_recs = [r for r in records if r.record_type == RecordType.NS]
    if ns_recs:
        ns_list = ", ".join([r.data for r in ns_recs])
        output += f"NS: {ns_list}\n"

    mx_recs = [r for r in records if r.record_type == RecordType.MX]
    if mx_recs:
        mx_list = ", ".join([f"{r.priority} {r.data}" for r in mx_recs])
        output += f"MX: {mx_list}\n"

    return output


def main():
    print("\n[DNS] INITIALIZING DNS INFRASTRUCTURE...\n")

    # Create authoritative servers for each domain
    auth_google = AuthoritativeDNSServer("google.com")
    auth_facebook = AuthoritativeDNSServer("facebook.com")
    auth_github = AuthoritativeDNSServer("github.com")
    auth_youtube = AuthoritativeDNSServer("youtube.com")
    auth_stackoverflow = AuthoritativeDNSServer("stackoverflow.com")

    auth_servers = {
        "google.com": auth_google,
        "facebook.com": auth_facebook,
        "github.com": auth_github,
        "youtube.com": auth_youtube,
        "stackoverflow.com": auth_stackoverflow,
    }

    print("Authoritative Servers Created:")
    print("1. google.com")
    print("2. facebook.com")
    print("3. github.com")
    print("4. youtube.com")
    print("5. stackoverflow.com")

    # Register all domains under the .com TLD
    tld_com = TLDServer(".com")
    tld_com.register_domain("google.com", auth_google)
    tld_com.register_domain("facebook.com", auth_facebook)
    tld_com.register_domain("github.com", auth_github)
    tld_com.register_domain("youtube.com", auth_youtube)
    tld_com.register_domain("stackoverflow.com", auth_stackoverflow)

    print("\nTLD Server Created: .com")
    print("  Registered domains: google.com, facebook.com, github.com, youtube.com, stackoverflow.com")

    root_server = RootDNSServer()
    root_server.register_tld(".com", tld_com)

    print("\nRoot DNS Server Created")

    local_server = LocalDNSServer("dns.poly.edu", cache_size=5)
    local_server.set_root_server(root_server)

    print("Local DNS Server Created.)")
    print("Cache size: 5 entries LRU Evicition\n")

    client = DNSClient(local_server)

    domains = [
        "google.com",
        "facebook.com",
        "github.com",
        "youtube.com",
        "stackoverflow.com",
    ]

    for i in range(1, 6):
        domain = domains[i - 1]
        auth = auth_servers[domain]

        if i % 2 != 0:
            print(f"\nQUERY : {i} ")
            print("-" * 70)
            records = client.resolve_iterative(domain, RecordType.A)
        else:
            print(f"\nQUERY: {i} ")
            print("-" * 70)
            records = client.resolve_recursive(domain, RecordType.A)

        if records:
            print("\nFINAL RESULT:")
            print(print_dns_records(domain, records +
                  auth.records.get(RecordType.NS, []) +
                  auth.records.get(RecordType.MX, []) +
                  auth.records.get(RecordType.A, [])))

        print("=" * 70)
    print("\nTEST: CACHE HIT FOR google.com")
    print(client.resolve_iterative("google.com", RecordType.A))

if __name__ == "__main__":
    main()
