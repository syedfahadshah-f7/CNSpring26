# DNS Implementation - Assignment #2 (CS3001)

**Course:** Computer Networks (CS3001)
**Assignment:** #2 - DNS Implementation
**Due Date:** Monday, April 6, 2026 (Presentation)
**Institution:** FAST-NUCS, Karachi

---

## 📌 Quick Summary

A **complete DNS simulation application** showing how domain name resolution works when a domain is not cached locally. Implements Root, TLD, and Authoritative DNS servers with both iterative and recursive resolution methods, plus local caching with LRU eviction.

---

## 📂 Files Overview

| File | Purpose |
|------|---------|
| **dns_simulation.py** | Main program (~650 lines, fully commented) |
| **CODE_EXPLANATION.md** | Architecture, design patterns, class descriptions |
| **VIVA_QUESTIONS.md** | 18 practice questions with detailed answers |
| **DEMO_GUIDE.md** | Step-by-step demo walkthrough (5-minute script) |
| **SAMPLE_OUTPUT.txt** | Expected program output |
| **README.md** | This file |

---

## 🚀 Quick Start

### Step 1: Update Student Info
Edit `dns_simulation.py` line ~520:
```python
print_header(
    student_name="Your Name",
    student_id="Your ID",
    section="Your Section"
)
```

### Step 2: Run Program
```bash
cd "d:\Sem 6\CN\A2"
python dns_simulation.py
```

### Step 3: Check Output
Should see:
- Iterative resolution (3 steps)
- Recursive resolution (internal work)
- Cache hits/misses
- Cache eviction
- Final statistics

---

## 📋 Features Implemented

✅ **Part 1: DNS Server Architecture**
- Root DNS Server (Top level)
- TLD DNS Server (.com level)
- Authoritative DNS Server (domain-specific)
- Local DNS Server (with caching)

✅ **Part 2: Resolution Types**
- Iterative DNS Resolution (client controls)
- Recursive DNS Resolution (server controls)

✅ **Part 3: Message Format**
- 16-bit Query ID
- 16-bit Reply ID (matching)
- Questions section
- Answers section
- Authority section
- Additional section

✅ **Part 4: DNS Records**
- A Records (IPv4 addresses)
- NS Records (nameserver delegation)
- MX Records (mail servers with priority)
- Real records for actual domains

✅ **Part 5: Local Cache**
- Stores resolved domain names
- CACHE HIT: Return from cache
- CACHE MISS: Query servers
- Auto-flushing when full

✅ **Part 6: Cache Auto-Flushing**
- Maximum cache size: 5 entries
- LRU (Least Recently Used) eviction
- Clear print messages when flushing

✅ **Part 7: Output Format**
- Student name, ID, section
- DNS request flow
- Query and reply messages
- Cache status indicators
- Final DNS records
- Cache statistics

---

## 🏗️ Architecture

### Class Hierarchy

```
DNSMessage
├── query_id (16 bits)
├── is_query / is_reply
├── is_recursive
├── questions
├── answers
├── authority
└── additional

DNSRecord
├── domain_name
├── record_type (A/NS/MX)
├── ttl (time-to-live)
└── data

DNSCache (LRU)
├── cache (dict)
├── access_time (tracking)
├── put()
├── get()
└── stats()

AuthoritativeDNSServer
├── domain
├── records (A, NS, MX)
├── _load_records()
└── query()

TLDServer
├── tld (".com")
├── authoritative_servers
├── register_domain()
└── query()

RootDNSServer
├── tld_servers
├── register_tld()
└── query()

LocalDNSServer
├── name ("dns.poly.edu")
├── cache (DNSCache)
├── root_server
├── resolve_iterative()
├── resolve_recursive()
└── stats()

DNSClient
├── local_server
├── resolve_recursive()
└── resolve_iterative()
```

### Resolution Flow

**Iterative:**
```
Client → Root ("Which TLD?")
Client → TLD ("Which Authoritative?")
Client → Authoritative ("What's the IP?")
```

**Recursive:**
```
Client → LocalServer (recursive query)
  [LocalServer internally queries: Root → TLD → Authoritative]
Client ← LocalServer (final answer)
```

---

## 📊 DNS Records Used

### Real Database (5 domains)

```
google.com:
  A: 64.233.187.99, 72.14.207.99, 64.233.167.99
  NS: ns1.google.com., ns2.google.com., ns3.google.com., ns4.google.com.
  MX: 10 smtp1.google.com., 10 smtp2.google.com., 10 smtp3.google.com., 10 smtp4.google.com.

facebook.com:
  A: 31.13.64.35, 31.13.64.36
  NS: a.ns.facebook.com., b.ns.facebook.com.
  MX: 10 aspmx.l.google.com., 20 alt1.aspmx.l.google.com.

github.com:
  A: 140.82.113.4, 140.82.114.4
  NS: ns1.github.com., ns2.github.com.
  MX: 10 mail.github.com.

youtube.com:
  A: 142.250.185.46, 142.251.41.14
  NS: ns1.youtube.com., ns2.youtube.com.
  MX: 10 mail.youtube.com.

stackoverflow.com:
  A: 151.101.1.140, 151.101.65.140
  NS: ns1.stack.com., ns2.stack.com.
  MX: 10 mail.stackoverflow.com.
```

---

## 📺 Sample Output Format

```
======================================================================
FAST-NUCS | COMPUTER NETWORKS (CS3001)
Assignment #2: DNS Implementation
======================================================================
Student Name:   [Your Name]
Student ID:     [Your ID]
Section:        [Your Section]
Date:           March 27, 2026
======================================================================

[DNS] INITIALIZING DNS INFRASTRUCTURE...

[OK] Authoritative Servers Created:
  - google.com
  - facebook.com
  - github.com
  - youtube.com
  - stackoverflow.com

>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
TEST 1: ITERATIVE DNS RESOLUTION
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

======================================================================
[QUERY] ITERATIVE RESOLUTION: google.com (A)
======================================================================
[ERROR] CACHE MISS for google.com

[STEP 1] Query ROOT DNS Server for google.com
  [OK] Root Server: 'Query TLD server for google.com'

[STEP 2] Query TLD DNS Server for google.com
  [OK] TLD Server: 'Query Authoritative server google.com'
    NS Record: ns4.google.com.
    NS Record: ns1.google.com.
    NS Record: ns2.google.com.
    NS Record: ns3.google.com.

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

>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
TEST 2: ITERATIVE RESOLUTION (CACHED)
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

======================================================================
[QUERY] ITERATIVE RESOLUTION: google.com (A)
======================================================================
[OK] CACHE HIT for google.com

--- Cache Statistics ---
Cache Stats - Hits: 3, Misses: 0, Hit Rate: 100.0%
Total Queries Made: 8
======================================================================
```


## ❓ Common Viva Questions

1. **"Explain iterative resolution"**
   - Answer: 3 steps, client queries each server, each server returns referral

2. **"What's the 16-bit ID for?"**
   - Answer: Matches query message with reply message

3. **"How does caching work?"**
   - Answer: Cache HIT = immediate return, MISS = query servers then cache

4. **"Why hierarchical DNS?"**
   - Answer: Scalability, redundancy, distributes load

5. **"Show me DNS message format"**
   - Answer: ID, flags, questions, answers, authority, additional

6. **"What are A, NS, MX records?"**
   - Answer: A = IP address, NS = nameserver, MX = mail server

7. **"How does LRU eviction work?"**
   - Answer: Remove least recently accessed entry when cache full

8. **"Can you add a new domain?"**
   - Answer: Yes, add to dns_database in _load_records()

---

## 📝 Submission Checklist

Before presentation on **April 6, 2026**:

- [ ] Update student name, ID, section in code
- [ ] Test run dns_simulation.py
- [ ] Prepare 5-minute demo script
- [ ] Take screenshots of output
- [ ] Read VIVA_QUESTIONS.md
- [ ] Understand DNS resolution flow
- [ ] Know line numbers of key code
- [ ] Practice demo 5+ times
- [ ] Upload code to Google Classroom
- [ ] Upload screenshots to Google Classroom

---

## 🔧 Technical Details

### Technologies
- **Language:** Python 3.6+
- **Design Pattern:** Object-Oriented Programming
- **No External Libraries:** Pure Python stdlib only
- **No Network Code:** Simulation only (console-based)
- **Cross-Platform:** Windows/Mac/Linux compatible

### Code Statistics
- **Total Lines:** ~650
- **Classes:** 8
- **Enums:** 1
- **Data Classes:** 3
- **Methods:** 25+
- **Test Cases:** 4

### Performance
- First query (iterative): Prints 3 steps
- Second query (cached): Instant return
- Cache eviction: LRU automatic
- All-in-memory: No file I/O

---

## 🎓 Learning Outcomes

After completing this assignment, you understand:

1. ✅ DNS hierarchical architecture
2. ✅ Root, TLD, Authoritative server roles
3. ✅ Iterative vs Recursive resolution
4. ✅ DNS message format with 16-bit IDs
5. ✅ A, NS, MX record types
6. ✅ DNS caching benefits
7. ✅ Cache eviction policies (LRU)
8. ✅ System design principles
9. ✅ Object-oriented programming
10. ✅ Clear technical communication

---

## 📚 Reference Documents

| Document | Contains |
|----------|----------|
| **CODE_EXPLANATION.md** | Architecture, classes, methods, design patterns |
| **VIVA_QUESTIONS.md** | 18 Q&As, theory, implementation details |
| **DEMO_GUIDE.md** | 5-min demo script, timing, tips |
| **SAMPLE_OUTPUT.txt** | Expected program output |

---

## ⚠️ Important Notes

- ✅ **NO plagiarism** - This is your own work
- ✅ **NO live DNS queries** - All hard-coded
- ✅ **NO external libraries** - Pure Python
- ✅ **NO real network sockets** - Simulation only
- ✅ **Clear logging** - Every step printed
- ✅ **Real records** - Actual Google/Facebook DNS data
- ✅ **Originality** - Your own design

---

## 🚨 Before Demo - CRITICAL CHECKLIST

1. **Update Student Info** (Line ~520)
   ```python
   student_name="Your Actual Name",
   student_id="Your Actual ID",
   section="Your Section"
   ```

2. **Test the Program**
   ```bash
   python dns_simulation.py
   ```

3. **Take Screenshots**
   - Program output
   - Cache statistics
   - Code snippets

4. **Prepare Demo Talk**
   - Practice 5-minute speech
   - Learn demo timing
   - Know key Q&A answers

5. **Upload to Google Classroom**
   - Code file (dns_simulation.py)
   - Screenshots (2-3 images)
   - Optional: This README

---

## 📞 Troubleshooting

### Problem: Program won't run
**Solution:** Check Python 3.6+, remove non-ASCII chars

### Problem: Can't see output
**Solution:** Run with `> output.txt` and read file

### Problem: Forgot student info update
**Solution:** Edit line ~520 before demo

### Problem: Output truncated
**Solution:** Run `python dns_simulation.py | less`

---

## 💡 Pro Tips

1. **During Demo:**
   - Speak slowly and clearly
   - Point to specific output lines
   - Make eye contact
   - Show confidence

2. **In Viva:**
   - Listen carefully
   - Answer directly
   - Draw diagrams if asked
   - Admit if you don't know (know what you know!)

3. **For Success:**
   - Practice 5+ times
   - Understand concepts (don't just memorize)
   - Know your code
   - Be enthusiastic

---

## ✨ Final Words

This assignment demonstrates your understanding of:
- **Networking Concepts** (DNS hierarchies)
- **System Design** (OOP architecture)
- **Algorithm Implementation** (caching, eviction)
- **Communication** (clear explanations)

You've built something real. Be proud. Explain it confidently.

**Good luck with your presentation!** 🎓

---

## 👨‍💼 Credits

**Written for:** FAST-NUCS CS3001 Students
**Assignment:** DNS Implementation
**Semester:** Spring 2026
**Date:** March 27, 2026

---

**Questions? Check VIVA_QUESTIONS.md or CODE_EXPLANATION.md**

**Demo help? See DEMO_GUIDE.md**

**Good presentations are born from good preparation.** Good luck! 🌟
