"""
modules/assessment_catalog.py
=============================
Catalog data for the revamped Skill Assessment page:
  1. GENERAL_QUIZZES: 10 distinct topic quizzes (Aptitude, Coding & DSA,
     HR Interview, Git, GitHub, DBMS & SQL, Operating Systems,
     Computer Networks, OOP & System Design, Logical Reasoning & Verbal).
  2. COMPANIES: 30 company-specific placement profiles (Service Based,
     Product & Tech, Consulting & FinTech) with About, Recruitment Process,
     Eligibility, Selection Process, CTC Breakdown, Topics Covered,
     Important Notes, and Sample Questions with Solutions.
"""

# ---------------------------------------------------------------------------
# 1. General Mode: 10 Topic Quizzes (5 MCQs each = 50 curated questions)
# ---------------------------------------------------------------------------
GENERAL_QUIZZES = [
    {
        "slug": "aptitude",
        "title": "Aptitude & Quantitative",
        "icon": "🧮",
        "category_key": "aptitude",
        "difficulty": "Standard",
        "estimated_minutes": 8,
        "description": "Percentages, profit & loss, time & work, trains, and probability.",
        "topics": ["Percentages", "Profit & Loss", "Time & Work", "Speed & Distance", "Probability"],
        "questions": [
            {
                "id": "gen_apt_1",
                "number": 1,
                "topic": "Problems on Trains",
                "prompt": "A train running at 72 km/hr crosses a 260 m platform in 23 seconds. What is the length of the train?",
                "options": {"a": "180 m", "b": "200 m", "c": "220 m", "d": "240 m"},
                "answer": "b",
                "explanation": "72 km/hr = 72 * (5/18) = 20 m/s. Total distance = 20 * 23 = 460 m. Train length = 460 - 260 = 200 m.",
            },
            {
                "id": "gen_apt_2",
                "number": 2,
                "topic": "Time & Work",
                "prompt": "A can complete a task in 12 days and B can complete it in 18 days. Working together, in how many days will they finish the task?",
                "options": {"a": "6.5 days", "b": "7.2 days", "c": "8.0 days", "d": "9.0 days"},
                "answer": "b",
                "explanation": "Combined rate = 1/12 + 1/18 = 5/36 per day. Time = 36/5 = 7.2 days.",
            },
            {
                "id": "gen_apt_3",
                "number": 3,
                "topic": "Profit & Loss",
                "prompt": "A shopkeeper marks an item 40% above cost price and offers a 20% discount. What is his net profit percentage?",
                "options": {"a": "10%", "b": "12%", "c": "15%", "d": "20%"},
                "answer": "b",
                "explanation": "Let CP = 100. MP = 140. SP = 140 * 0.80 = 112. Profit = 12%.",
            },
            {
                "id": "gen_apt_4",
                "number": 4,
                "topic": "Percentages",
                "prompt": "If the price of sugar increases by 25%, by what percentage must a household reduce consumption to keep expenditure unchanged?",
                "options": {"a": "15%", "b": "20%", "c": "25%", "d": "30%"},
                "answer": "b",
                "explanation": "Reduction % = (25 / (100 + 25)) * 100 = (25 / 125) * 100 = 20%.",
            },
            {
                "id": "gen_apt_5",
                "number": 5,
                "topic": "Probability",
                "prompt": "Two fair dice are thrown simultaneously. What is the probability of getting a sum equal to 9?",
                "options": {"a": "1/6", "b": "1/9", "c": "1/12", "d": "5/36"},
                "answer": "b",
                "explanation": "Favorable outcomes: (3,6), (4,5), (5,4), (6,3) = 4 out of 36. Probability = 4/36 = 1/9.",
            },
        ],
    },
    {
        "slug": "coding",
        "title": "Coding & DSA",
        "icon": "💻",
        "category_key": "coding",
        "difficulty": "Standard",
        "estimated_minutes": 10,
        "description": "Data structures, algorithms, recursion, trees, and time complexity.",
        "topics": ["Arrays & Hashing", "Stacks & Queues", "Trees & Graphs", "Sorting", "Big-O Complexity"],
        "questions": [
            {
                "id": "gen_code_1",
                "number": 1,
                "topic": "Time Complexity",
                "prompt": "What is the worst-case time complexity of searching for an element in a balanced Binary Search Tree (AVL / Red-Black) with N nodes?",
                "options": {"a": "O(1)", "b": "O(log N)", "c": "O(N)", "d": "O(N log N)"},
                "answer": "b",
                "explanation": "A balanced BST maintains height O(log N), so search takes O(log N) in the worst case.",
            },
            {
                "id": "gen_code_2",
                "number": 2,
                "topic": "Stacks",
                "prompt": "Which data structure is best suited for evaluating a postfix (Reverse Polish Notation) expression?",
                "options": {"a": "Queue", "b": "Stack", "c": "Min-Heap", "d": "Hash Map"},
                "answer": "b",
                "explanation": "Operands are pushed onto a stack, and operators pop the top two operands to compute and push the result.",
            },
            {
                "id": "gen_code_3",
                "number": 3,
                "topic": "Sorting",
                "prompt": "Which sorting algorithm guarantees O(N log N) worst-case time complexity and is stable?",
                "options": {"a": "Quick Sort", "b": "Heap Sort", "c": "Merge Sort", "d": "Selection Sort"},
                "answer": "c",
                "explanation": "Merge Sort always runs in O(N log N) time and preserves the relative order of equal elements.",
            },
            {
                "id": "gen_code_4",
                "number": 4,
                "topic": "Graphs",
                "prompt": "Which algorithm finds the shortest path from a single source to all vertices in a graph with non-negative edge weights?",
                "options": {"a": "Kruskal's Algorithm", "b": "Dijkstra's Algorithm", "c": "Prim's Algorithm", "d": "Topological Sort"},
                "answer": "b",
                "explanation": "Dijkstra's greedy algorithm computes single-source shortest paths when all edge weights are >= 0.",
            },
            {
                "id": "gen_code_5",
                "number": 5,
                "topic": "Dynamic Programming",
                "prompt": "Which two properties must a problem satisfy to be solved effectively using Dynamic Programming?",
                "options": {
                    "a": "Greedy choice & Divide and Conquer",
                    "b": "Optimal substructure & Overlapping subproblems",
                    "c": "Backtracking & Memoization only",
                    "d": "Linearity & Monotonicity",
                },
                "answer": "b",
                "explanation": "Dynamic Programming applies when optimal solutions to subproblems compose the global optimum and subproblems repeat.",
            },
        ],
    },
    {
        "slug": "hr",
        "title": "HR Interview & Behavioral",
        "icon": "🤝",
        "category_key": "hr",
        "difficulty": "Standard",
        "estimated_minutes": 7,
        "description": "STAR framework, conflict resolution, leadership, and workplace ethics.",
        "topics": ["STAR Method", "Team Conflict", "Strengths & Weaknesses", "Ownership", "Communication"],
        "questions": [
            {
                "id": "gen_hr_1",
                "number": 1,
                "topic": "STAR Framework",
                "prompt": "In the STAR behavioral interview framework, what does the 'R' stand for?",
                "options": {"a": "Reason", "b": "Result", "c": "Responsibility", "d": "Review"},
                "answer": "b",
                "explanation": "STAR stands for Situation, Task, Action, and Result — emphasizing measurable outcomes of your actions.",
            },
            {
                "id": "gen_hr_2",
                "number": 2,
                "topic": "Conflict Resolution",
                "prompt": "A teammate disagrees strongly with your technical approach right before a sprint deadline. What is the best professional response?",
                "options": {
                    "a": "Escalate immediately to upper management without discussing",
                    "b": "Listen to their concerns objectively, compare trade-offs with data, and align on the safest deliverable",
                    "c": "Silently implement your approach anyway",
                    "d": "Delay the sprint indefinitely",
                },
                "answer": "b",
                "explanation": "Constructive, data-driven collaboration respects teammates while keeping project goals on track.",
            },
            {
                "id": "gen_hr_3",
                "number": 3,
                "topic": "Self-Awareness",
                "prompt": "When asked 'What is your biggest weakness?' in an HR interview, which approach is strongest?",
                "options": {
                    "a": "Claiming you have no weaknesses",
                    "b": "Using a cliché like 'I work too hard'",
                    "c": "Sharing a genuine, non-critical skill gap and concrete steps you are taking to improve it",
                    "d": "Listing a core requirement of the job as a weakness",
                },
                "answer": "c",
                "explanation": "Interviewers value honesty, self-awareness, and proactive growth.",
            },
            {
                "id": "gen_hr_4",
                "number": 4,
                "topic": "Ownership",
                "prompt": "You discover a bug in production caused by a commit you pushed. What should you do first?",
                "options": {
                    "a": "Wait to see if anyone notices",
                    "b": "Blame unclear requirements from QA",
                    "c": "Acknowledge it promptly, alert the team, and work on a fix or rollback",
                    "d": "Quietly revert it without telling anyone",
                },
                "answer": "c",
                "explanation": "High ownership means transparent communication and rapid remediation to protect users.",
            },
            {
                "id": "gen_hr_5",
                "number": 5,
                "topic": "Company Fit",
                "prompt": "When asked 'Why do you want to join our company?', what makes an answer stand out?",
                "options": {
                    "a": "Mentioning only the salary package",
                    "b": "Connecting the company's products, engineering culture, and role to your specific skills and career goals",
                    "c": "Saying you applied everywhere and got an interview here",
                    "d": "Reciting the company's Wikipedia founding date",
                },
                "answer": "b",
                "explanation": "Tailored alignment between your background and the company's mission shows genuine motivation.",
            },
        ],
    },
    {
        "slug": "git",
        "title": "Git Version Control",
        "icon": "🌿",
        "category_key": "technical",
        "difficulty": "Standard",
        "estimated_minutes": 8,
        "description": "Commits, branching, merging vs rebasing, stashing, reset, and cherry-pick.",
        "topics": ["Staging & Commits", "Branching", "Merge vs Rebase", "Reset & Revert", "Git Stash"],
        "questions": [
            {
                "id": "gen_git_1",
                "number": 1,
                "topic": "Staging",
                "prompt": "Which command moves modified files from the working directory into the Git staging area (index)?",
                "options": {"a": "git commit", "b": "git add", "c": "git push", "d": "git stage-all"},
                "answer": "b",
                "explanation": "`git add <path>` stages changes in the index so they are included in the next commit.",
            },
            {
                "id": "gen_git_2",
                "number": 2,
                "topic": "Undo Changes",
                "prompt": "Which command safely undoes a commit on a shared remote branch by creating a new inverse commit instead of rewriting history?",
                "options": {"a": "git reset --hard HEAD~1", "b": "git revert <commit>", "c": "git rebase -i", "d": "git clean -fd"},
                "answer": "b",
                "explanation": "`git revert` creates a new commit that negates an earlier commit, preserving shared commit history.",
            },
            {
                "id": "gen_git_3",
                "number": 3,
                "topic": "Branching",
                "prompt": "What does `git switch -c feature/login` (or `git checkout -b feature/login`) do?",
                "options": {
                    "a": "Deletes the feature/login branch",
                    "b": "Creates a new branch named feature/login and switches to it",
                    "c": "Merges feature/login into main",
                    "d": "Pushes feature/login to origin",
                },
                "answer": "b",
                "explanation": "Both `git switch -c` and `git checkout -b` create a new branch and immediately check it out.",
            },
            {
                "id": "gen_git_4",
                "number": 4,
                "topic": "Stashing",
                "prompt": "You have uncommitted work on a branch and need to switch branches urgently without committing. Which command temporarily saves your changes?",
                "options": {"a": "git stash", "b": "git cherry-pick", "c": "git bisect", "d": "git tag"},
                "answer": "a",
                "explanation": "`git stash` saves dirty working directory and index changes onto a stack so you can reapply them later.",
            },
            {
                "id": "gen_git_5",
                "number": 5,
                "topic": "Rebase vs Merge",
                "prompt": "What is the primary difference between `git merge` and `git rebase`?",
                "options": {
                    "a": "Merge deletes the feature branch automatically; rebase does not",
                    "b": "Merge preserves branching history with a merge commit; rebase replays commits linearly on top of the target branch",
                    "c": "Rebase only works on remote repositories",
                    "d": "Merge cannot resolve conflicts",
                },
                "answer": "b",
                "explanation": "Rebase creates a linear commit history by replaying commits onto a new base, whereas merge joins histories.",
            },
        ],
    },
    {
        "slug": "github",
        "title": "GitHub & Collaboration",
        "icon": "🐙",
        "category_key": "technical",
        "difficulty": "Standard",
        "estimated_minutes": 8,
        "description": "Pull Requests, forks, GitHub Actions CI/CD, branch protection, and code reviews.",
        "topics": ["Pull Requests", "Forks & Upstreams", "GitHub Actions", "Branch Protection", "Issues & Reviews"],
        "questions": [
            {
                "id": "gen_gh_1",
                "number": 1,
                "topic": "Open Source Workflow",
                "prompt": "When contributing to a GitHub repository where you do not have write access, what is the standard workflow?",
                "options": {
                    "a": "Push directly to main",
                    "b": "Fork the repo, create a feature branch, push to your fork, and open a Pull Request",
                    "c": "Download the ZIP and email it to the maintainer",
                    "d": "Use git force-push on origin/main",
                },
                "answer": "b",
                "explanation": "Forking creates your own remote copy so you can propose changes safely via a Pull Request.",
            },
            {
                "id": "gen_gh_2",
                "number": 2,
                "topic": "GitHub Actions",
                "prompt": "Where must GitHub Actions workflow YAML files be stored in a repository to be recognized by GitHub?",
                "options": {"a": ".github/actions/", "b": ".github/workflows/", "c": "workflows/", "d": ".ci/github/"},
                "answer": "b",
                "explanation": "GitHub automatically discovers and runs CI/CD workflow files placed inside `.github/workflows/`.",
            },
            {
                "id": "gen_gh_3",
                "number": 3,
                "topic": "Branch Protection",
                "prompt": "Which GitHub repository setting prevents direct pushes to `main` and requires passing CI checks and peer approvals first?",
                "options": {"a": "GitHub Pages", "b": "Branch Protection Rules / Rulesets", "c": "Dependabot Alerts", "d": "Repository Insights"},
                "answer": "b",
                "explanation": "Branch protection rules enforce PR reviews, status checks, and block force pushes on protected branches.",
            },
            {
                "id": "gen_gh_4",
                "number": 4,
                "topic": "Pull Request Merge Options",
                "prompt": "Which GitHub PR merge strategy combines all commits from a feature branch into a single commit on the base branch?",
                "options": {"a": "Create a merge commit", "b": "Squash and merge", "c": "Rebase and merge", "d": "Fast-forward only"},
                "answer": "b",
                "explanation": "'Squash and merge' condenses all PR commits into one clean commit on the target branch.",
            },
            {
                "id": "gen_gh_5",
                "number": 5,
                "topic": "Issue Linking",
                "prompt": "Which keyword in a Pull Request description automatically closes GitHub Issue #42 when the PR is merged into the default branch?",
                "options": {"a": "Ref #42", "b": "Fixes #42", "c": "Mentions #42", "d": "See #42"},
                "answer": "b",
                "explanation": "Keywords like `Fixes #42`, `Closes #42`, or `Resolves #42` auto-close the linked issue upon merge.",
            },
        ],
    },
    {
        "slug": "dbms",
        "title": "DBMS & SQL",
        "icon": "🗄️",
        "category_key": "technical",
        "difficulty": "Standard",
        "estimated_minutes": 8,
        "description": "Normalization, ACID properties, SQL joins, indexing, and transactions.",
        "topics": ["Normalization", "ACID Properties", "SQL Joins", "Indexing", "Keys"],
        "questions": [
            {
                "id": "gen_db_1",
                "number": 1,
                "topic": "ACID Properties",
                "prompt": "In database transactions, what does 'Isolation' guarantee?",
                "options": {
                    "a": "Committed data survives power failure",
                    "b": "Concurrent transactions do not interfere with each other's intermediate state",
                    "c": "All constraints remain valid after commit",
                    "d": "Transactions execute all-or-nothing",
                },
                "answer": "b",
                "explanation": "Isolation ensures concurrent execution leaves the database in the same state as serial execution.",
            },
            {
                "id": "gen_db_2",
                "number": 2,
                "topic": "Normalization",
                "prompt": "A table in 2NF is in Third Normal Form (3NF) if it has no:",
                "options": {
                    "a": "Primary keys",
                    "b": "Transitive functional dependencies of non-key attributes on the primary key",
                    "c": "Foreign keys",
                    "d": "Composite keys",
                },
                "answer": "b",
                "explanation": "3NF eliminates transitive dependencies (A -> B -> C) where non-prime attributes depend on other non-prime attributes.",
            },
            {
                "id": "gen_db_3",
                "number": 3,
                "topic": "SQL Clauses",
                "prompt": "Which SQL clause filters groups created by `GROUP BY`?",
                "options": {"a": "WHERE", "b": "HAVING", "c": "ORDER BY", "d": "DISTINCT"},
                "answer": "b",
                "explanation": "`WHERE` filters rows before grouping, while `HAVING` filters aggregated groups after `GROUP BY`.",
            },
            {
                "id": "gen_db_4",
                "number": 4,
                "topic": "SQL Joins",
                "prompt": "Which join returns all rows from the left table and matching rows from the right table (with NULLs when unmatched)?",
                "options": {"a": "INNER JOIN", "b": "LEFT OUTER JOIN", "c": "RIGHT OUTER JOIN", "d": "CROSS JOIN"},
                "answer": "b",
                "explanation": "LEFT OUTER JOIN preserves every row from the left table regardless of whether a match exists on the right.",
            },
            {
                "id": "gen_db_5",
                "number": 5,
                "topic": "Indexing",
                "prompt": "Which data structure is most commonly used by relational databases for general-purpose table indexes?",
                "options": {"a": "Stack", "b": "B+ Tree", "c": "Linked List", "d": "Adjacency Matrix"},
                "answer": "b",
                "explanation": "B+ Trees minimize disk I/O and support fast equality lookups as well as range queries.",
            },
        ],
    },
    {
        "slug": "os",
        "title": "Operating Systems",
        "icon": "⚙️",
        "category_key": "technical",
        "difficulty": "Standard",
        "estimated_minutes": 8,
        "description": "Processes vs threads, CPU scheduling, deadlocks, paging, and virtual memory.",
        "topics": ["CPU Scheduling", "Deadlocks", "Virtual Memory", "Paging", "Synchronization"],
        "questions": [
            {
                "id": "gen_os_1",
                "number": 1,
                "topic": "Deadlocks",
                "prompt": "Which of the following is NOT one of the four Coffman conditions required for a deadlock?",
                "options": {"a": "Mutual Exclusion", "b": "Hold and Wait", "c": "Preemption", "d": "Circular Wait"},
                "answer": "c",
                "explanation": "Deadlock requires *No Preemption* (alongside Mutual Exclusion, Hold and Wait, and Circular Wait).",
            },
            {
                "id": "gen_os_2",
                "number": 2,
                "topic": "Virtual Memory",
                "prompt": "What is 'thrashing' in an operating system?",
                "options": {
                    "a": "A CPU running at 100% idle",
                    "b": "Excessive paging activity where the system spends more time swapping pages than executing instructions",
                    "c": "Deleting temporary files on boot",
                    "d": "Running multiple threads on one core",
                },
                "answer": "b",
                "explanation": "Thrashing occurs when working sets exceed physical RAM, causing constant page faults and disk swapping.",
            },
            {
                "id": "gen_os_3",
                "number": 3,
                "topic": "Processes & Threads",
                "prompt": "Which resource is shared among all threads of the same process?",
                "options": {"a": "Program Counter", "b": "Thread Stack", "c": "Heap & Address Space", "d": "CPU Registers"},
                "answer": "c",
                "explanation": "Threads share the process's heap, global data, and code segment, while each thread has its own stack and registers.",
            },
            {
                "id": "gen_os_4",
                "number": 4,
                "topic": "CPU Scheduling",
                "prompt": "Which scheduling algorithm is specifically designed for time-sharing systems using a fixed time quantum?",
                "options": {"a": "FCFS", "b": "Shortest Job First", "c": "Round Robin", "d": "Priority Non-Preemptive"},
                "answer": "c",
                "explanation": "Round Robin assigns each ready process a fixed time slice (quantum) in circular order.",
            },
            {
                "id": "gen_os_5",
                "number": 5,
                "topic": "Memory Management",
                "prompt": "What hardware component translates virtual memory addresses into physical addresses?",
                "options": {"a": "ALU", "b": "MMU (Memory Management Unit)", "c": "DMA Controller", "d": "BIOS"},
                "answer": "b",
                "explanation": "The MMU (with the TLB cache) performs virtual-to-physical address translation.",
            },
        ],
    },
    {
        "slug": "cn",
        "title": "Computer Networks",
        "icon": "🌐",
        "category_key": "technical",
        "difficulty": "Standard",
        "estimated_minutes": 8,
        "description": "OSI layers, TCP vs UDP, HTTP/HTTPS, DNS, and IP subnetting.",
        "topics": ["OSI Model", "TCP vs UDP", "HTTP & HTTPS", "DNS", "Subnetting"],
        "questions": [
            {
                "id": "gen_cn_1",
                "number": 1,
                "topic": "OSI Model",
                "prompt": "At which layer of the OSI model do routers primarily operate to forward packets using IP addresses?",
                "options": {"a": "Data Link Layer (Layer 2)", "b": "Network Layer (Layer 3)", "c": "Transport Layer (Layer 4)", "d": "Session Layer (Layer 5)"},
                "answer": "b",
                "explanation": "Routers inspect IP headers and make forwarding decisions at the Network Layer (Layer 3).",
            },
            {
                "id": "gen_cn_2",
                "number": 2,
                "topic": "Transport Layer",
                "prompt": "Which protocol provides connectionless, low-overhead delivery without guaranteed ordering or retransmission?",
                "options": {"a": "TCP", "b": "UDP", "c": "HTTP", "d": "TLS"},
                "answer": "b",
                "explanation": "UDP is connectionless and lightweight, ideal for video streaming, gaming, and DNS lookups.",
            },
            {
                "id": "gen_cn_3",
                "number": 3,
                "topic": "Ports",
                "prompt": "What is the default well-known port number for HTTPS traffic?",
                "options": {"a": "22", "b": "80", "c": "443", "d": "8080"},
                "answer": "c",
                "explanation": "HTTP uses port 80 by default, whereas encrypted HTTPS uses port 443.",
            },
            {
                "id": "gen_cn_4",
                "number": 4,
                "topic": "TCP Handshake",
                "prompt": "What is the correct sequence of flags in a TCP three-way handshake?",
                "options": {"a": "ACK -> SYN -> FIN", "b": "SYN -> SYN-ACK -> ACK", "c": "SYN -> ACK -> RST", "d": "FIN -> ACK -> SYN"},
                "answer": "b",
                "explanation": "Client sends SYN, server replies SYN-ACK, and client confirms with ACK.",
            },
            {
                "id": "gen_cn_5",
                "number": 5,
                "topic": "DNS",
                "prompt": "What is the primary purpose of the Domain Name System (DNS)?",
                "options": {
                    "a": "Encrypting HTTP payloads",
                    "b": "Translating human-readable domain names into IP addresses",
                    "c": "Assigning MAC addresses to NICs",
                    "d": "Compressing web assets",
                },
                "answer": "b",
                "explanation": "DNS resolves domain names (e.g. example.com) to their corresponding IPv4/IPv6 addresses.",
            },
        ],
    },
    {
        "slug": "oop",
        "title": "OOP & System Design",
        "icon": "🏛️",
        "category_key": "coding",
        "difficulty": "Standard",
        "estimated_minutes": 8,
        "description": "Polymorphism, SOLID principles, design patterns, caching, and load balancing.",
        "topics": ["Polymorphism", "SOLID Principles", "Design Patterns", "Caching", "Load Balancing"],
        "questions": [
            {
                "id": "gen_oop_1",
                "number": 1,
                "topic": "OOP Concepts",
                "prompt": "Which OOP mechanism allows a subclass to provide a specific implementation of a method already defined in its parent class?",
                "options": {"a": "Method Overloading", "b": "Method Overriding", "c": "Encapsulation", "d": "Aggregation"},
                "answer": "b",
                "explanation": "Method overriding enables runtime polymorphism by redefining a parent method in a child class.",
            },
            {
                "id": "gen_oop_2",
                "number": 2,
                "topic": "SOLID Principles",
                "prompt": "In SOLID principles, what does the 'S' (Single Responsibility Principle) state?",
                "options": {
                    "a": "A class should only have static methods",
                    "b": "A class should have only one reason to change",
                    "c": "Every module must be a singleton",
                    "d": "Subclasses must never extend base classes",
                },
                "answer": "b",
                "explanation": "SRP states that each class or module should encapsulate one cohesive responsibility.",
            },
            {
                "id": "gen_oop_3",
                "number": 3,
                "topic": "Design Patterns",
                "prompt": "Which design pattern ensures a class has only one instance and provides a global point of access to it?",
                "options": {"a": "Observer", "b": "Factory", "c": "Singleton", "d": "Decorator"},
                "answer": "c",
                "explanation": "The Singleton pattern restricts instantiation of a class to a single shared object.",
            },
            {
                "id": "gen_oop_4",
                "number": 4,
                "topic": "System Design",
                "prompt": "In distributed systems, what is the main role of a Reverse Proxy / Load Balancer?",
                "options": {
                    "a": "Compiling backend source code",
                    "b": "Distributing incoming client traffic across multiple backend servers for availability and scale",
                    "c": "Replacing the database",
                    "d": "Generating SSL keys on the client",
                },
                "answer": "b",
                "explanation": "Load balancers spread requests across healthy instances to prevent single points of overload.",
            },
            {
                "id": "gen_oop_5",
                "number": 5,
                "topic": "Caching",
                "prompt": "Which cache eviction policy removes the item that has not been accessed for the longest time?",
                "options": {"a": "FIFO", "b": "LIFO", "c": "LRU (Least Recently Used)", "d": "Random"},
                "answer": "c",
                "explanation": "LRU evicts the least recently accessed key first to keep hot data in cache.",
            },
        ],
    },
    {
        "slug": "logical",
        "title": "Logical Reasoning & Verbal",
        "icon": "🧩",
        "category_key": "aptitude",
        "difficulty": "Standard",
        "estimated_minutes": 8,
        "description": "Number series, syllogisms, blood relations, grammar, and verbal analogies.",
        "topics": ["Number Series", "Syllogisms", "Blood Relations", "Grammar", "Verbal Analogy"],
        "questions": [
            {
                "id": "gen_log_1",
                "number": 1,
                "topic": "Number Series",
                "prompt": "Find the next number in the series: 3, 7, 15, 31, 63, ?",
                "options": {"a": "95", "b": "125", "c": "127", "d": "131"},
                "answer": "c",
                "explanation": "Each term follows (previous * 2) + 1: 63 * 2 + 1 = 127.",
            },
            {
                "id": "gen_log_2",
                "number": 2,
                "topic": "Syllogisms",
                "prompt": "Statements: All engineers are problem-solvers. Some problem-solvers are artists. Which conclusion definitely follows?",
                "options": {
                    "a": "All artists are engineers",
                    "b": "Some engineers are artists",
                    "c": "All problem-solvers are engineers",
                    "d": "None of the above definitely follows",
                },
                "answer": "d",
                "explanation": "The overlap between problem-solvers and artists need not intersect with engineers, so none follows definitely.",
            },
            {
                "id": "gen_log_3",
                "number": 3,
                "topic": "Blood Relations",
                "prompt": "Pointing to a photograph, Ravi said, 'She is the daughter of my grandfather's only son.' How is the girl related to Ravi?",
                "options": {"a": "Cousin", "b": "Sister", "c": "Aunt", "d": "Mother"},
                "answer": "b",
                "explanation": "Ravi's grandfather's only son is Ravi's father. His father's daughter is Ravi's sister.",
            },
            {
                "id": "gen_log_4",
                "number": 4,
                "topic": "Grammar",
                "prompt": "Choose the grammatically correct sentence:",
                "options": {
                    "a": "Neither of the candidates have submitted their resume.",
                    "b": "Neither of the candidates has submitted their resume.",
                    "c": "Neither of the candidate has submitted his resume.",
                    "d": "Neither of the candidates were ready.",
                },
                "answer": "b",
                "explanation": "'Neither' takes a singular verb ('has') while 'of the candidates' uses the plural noun.",
            },
            {
                "id": "gen_log_5",
                "number": 5,
                "topic": "Coding-Decoding",
                "prompt": "If 'PLACEMENT' is coded as 'QMBDFNFOU', how is 'INTERN' coded in the same pattern?",
                "options": {"a": "JOUFSO", "b": "JOUFSP", "c": "KPUFSO", "d": "JNVFSO"},
                "answer": "a",
                "explanation": "Each letter is shifted forward by +1 in the alphabet: I->J, N->O, T->U, E->F, R->S, N->O.",
            },
        ],
    },
]

GENERAL_QUIZ_BY_SLUG = {q["slug"]: q for q in GENERAL_QUIZZES}


# ---------------------------------------------------------------------------
# 2. Company Specific Mode: 30 Companies with Detailed Profiles & Sample Qs
# ---------------------------------------------------------------------------
def _make_service_company(
    slug,
    name,
    about,
    role,
    ctc_total,
    ctc_items,
    eligibility,
    recruitment_process,
    topics_covered,
    important_note,
    exam_style,
    sample_questions,
    tier="Service Based",
    eligible_courses="B.E / B.Tech — CSE, ECE, EEE, IT, MCA",
    eligible_batch="2025 / 2026",
):
    return {
        "slug": slug,
        "name": name,
        "tier": tier,
        "tagline": f"{name} Placement Papers, Recruitment Process, CTC & Sample Questions",
        "about": about,
        "role": role,
        "eligible_courses": eligible_courses,
        "eligible_batch": eligible_batch,
        "eligibility": eligibility,
        "ctc_breakdown": {"total": ctc_total, "items": ctc_items},
        "recruitment_process": recruitment_process,
        "selection_process": recruitment_process,
        "topics_covered": topics_covered,
        "important_note": important_note,
        "exam_style": exam_style,
        "sample_questions": sample_questions,
    }


COMPANIES = [
    # ---- Featured Product & Tech Company (matching the video walkthrough) ----
    {
        "slug": "atlassian",
        "name": "Atlassian",
        "tier": "Product & Tech",
        "tagline": "Atlassian Coding Questions, Recruitment Process, CTC & Solutions",
        "about": (
            "Atlassian is an Australian software company that specializes in providing collaboration "
            "and development tools for teams and organizations. Founded in 2002 by Mike Cannon-Brookes "
            "and Scott Farquhar, its flagship products include Jira, Confluence, Trello, Bitbucket, and Jira Service Management.\n\n"
            "They operate on a subscription-based licensing model serving global engineering teams and went "
            "public on NASDAQ under the ticker symbol TEAM."
        ),
        "role": "Software Development Engineer (SDE)",
        "eligible_courses": "B.E / B.Tech — CSE, ECE, EE & IT",
        "eligible_batch": "2025 / 2026",
        "eligibility": [
            "Minimum 75% or equivalent CGPA required in 10th / 12th / Graduation.",
            "No active / current backlogs.",
        ],
        "ctc_breakdown": {
            "total": "₹ 80 LPA",
            "items": [
                {"label": "Base Pay", "value": "₹ 25 Lakhs"},
                {"label": "Signing Bonus", "value": "₹ 2 Lakhs"},
                {"label": "R.S.U (4-year vest)", "value": "₹ 60 Lakhs (₹ 15 Lakhs/year)"},
                {"label": "Performance Bonus", "value": "Up to 10% of Base Pay"},
            ],
        },
        "recruitment_process": [
            "1. Online Coding Assessment (HackerRank)",
            "2. Technical Interview (2 Rounds — DSA & System Design)",
            "3. Values & HR Interview",
        ],
        "selection_process": [
            "1. Online Coding Assessment",
            "2. Technical Interview",
            "3. Values & Management / HR Interview",
        ],
        "topics_covered": [
            "Data Structures & Algorithms (Strings, Sliding Window, Stacks, Trees, Graphs)",
            "OOPS Concepts & Clean Modular Code",
            "DBMS / SQL",
            "Computer Networks",
            "Operating Systems",
        ],
        "important_note": [
            "1st Round of Recruitment Process (Online Coding Assessment) is conducted on HackerRank for 90 Minutes.",
            "Steps in the selection procedure may vary slightly across campuses and regions.",
            "Please check the official Atlassian Careers page for the latest updates.",
        ],
        "exam_style": (
            "Hard product-company DSA & CS fundamentals: tricky string/array algorithms, binary search, "
            "sliding window, monotonic stacks, time/space complexity analysis, and concurrency/DBMS edge cases."
        ),
        "sample_questions": [
            {
                "title": "Question 1: Match Substring After Replacement",
                "problem": (
                    "Given two strings `s` and `sub`, along with a 2D character array `mappings`, determine if it is "
                    "possible to make `sub` a substring of `s` by replacing zero or more characters in `sub` using "
                    "mappings `[old, new]`. Each character in `sub` can be replaced at most once."
                ),
                "examples": [
                    'Input: s = "fool3e7bar", sub = "leet", mappings = [["e","3"],["t","7"],["t","8"]] -> Output: true',
                    'Input: s = "fooleetbar", sub = "f00l", mappings = [["0","o"]] -> Output: false',
                ],
                "explanation": (
                    "Build a lookup table `canReplace[old][new]` for all allowed character mappings. Slide a window "
                    "of length `len(sub)` across `s`; for each position `i`, verify that every character `sub[j]` either "
                    "equals `s[i+j]` or has `canReplace[sub[j]][s[i+j]] == true`. Time complexity: O(N * M)."
                ),
                "solutions": {
                    "cpp": """bool matchReplacement(string s, string sub, vector<vector<char>>& mappings) {
    bool allowed[256][256] = {false};
    for (auto& m : mappings) allowed[(unsigned char)m[0]][(unsigned char)m[1]] = true;
    int n = s.size(), m = sub.size();
    for (int i = 0; i <= n - m; ++i) {
        bool ok = true;
        for (int j = 0; j < m; ++j) {
            if (s[i + j] != sub[j] && !allowed[(unsigned char)sub[j]][(unsigned char)s[i + j]]) {
                ok = false; break;
            }
        }
        if (ok) return true;
    }
    return false;
}""",
                    "python": """def match_replacement(s: str, sub: str, mappings: list[list[str]]) -> bool:
    allowed = set((old, new) for old, new in mappings)
    n, m = len(s), len(sub)
    for i in range(n - m + 1):
        if all(s[i + j] == sub[j] or (sub[j], s[i + j]) in allowed for j in range(m)):
            return True
    return False""",
                    "java": """public boolean matchReplacement(String s, String sub, char[][] mappings) {
    boolean[][] allowed = new boolean[256][256];
    for (char[] m : mappings) allowed[m[0]][m[1]] = true;
    int n = s.length(), m = sub.length();
    for (int i = 0; i <= n - m; i++) {
        boolean ok = true;
        for (int j = 0; j < m; j++) {
            char a = sub.charAt(j), b = s.charAt(i + j);
            if (a != b && !allowed[a][b]) { ok = false; break; }
        }
        if (ok) return true;
    }
    return false;
}""",
                },
            },
            {
                "title": "Question 2: Queries for Count in Unsorted Array",
                "problem": (
                    "Given an unsorted integer array of size N and Q range queries `[L, R]`, count how many "
                    "elements in the array satisfy `L <= element <= R`."
                ),
                "examples": [
                    "Array = [1, 3, 3, 9, 10, 4], Query [1, 4] -> 4 (elements 1, 3, 3, 4); Query [9, 12] -> 2 (9, 10)."
                ],
                "explanation": (
                    "Sort the array once in O(N log N). For each query `[L, R]`, use binary search (`lower_bound` for L "
                    "and `upper_bound` for R) to answer in O(log N) per query."
                ),
                "solutions": {
                    "cpp": """int countInRange(vector<int>& arr, int L, int R) {
    auto lo = lower_bound(arr.begin(), arr.end(), L);
    auto hi = upper_bound(arr.begin(), arr.end(), R);
    return (int)(hi - lo);
}""",
                    "python": """from bisect import bisect_left, bisect_right

def count_in_range(sorted_arr: list[int], L: int, R: int) -> int:
    return bisect_right(sorted_arr, R) - bisect_left(sorted_arr, L)""",
                    "java": """// Sort arr first, then upperBound(arr, R) - lowerBound(arr, L) in O(log N).""",
                },
            },
            {
                "title": "Question 3: Smallest Window Containing All Characters",
                "problem": (
                    "Given two strings `S` and `P`, find the smallest substring in `S` that contains all characters "
                    "of `P` (including duplicates). Return `-1` if no such window exists."
                ),
                "examples": [
                    'Input: S = "timetopractice", P = "toc" -> Output: "toprac"'
                ],
                "explanation": (
                    "Use a two-pointer sliding window with character frequency counts. Expand the right pointer until all "
                    "required characters are covered, then shrink from the left while maintaining validity to record the minimum length."
                ),
                "solutions": {
                    "cpp": """// Maintain need[256] and have count; expand right, shrink left when formed == required.""",
                    "python": """from collections import Counter

def min_window(s: str, p: str) -> str:
    need = Counter(p)
    missing = len(p)
    left = start = end = 0
    for right, ch in enumerate(s, 1):
        if need[ch] > 0:
            missing -= 1
        need[ch] -= 1
        if missing == 0:
            while left < right and need[s[left]] < 0:
                need[s[left]] += 1
                left += 1
            if end == 0 or right - left < end - start:
                start, end = left, right
            need[s[left]] += 1
            missing += 1
            left += 1
    return s[start:end] if end else "-1" """,
                    "java": """// Sliding window with int[128] frequency array in O(|S| + |P|) time.""",
                },
            },
        ],
    },
    _make_service_company(
        slug="accenture",
        name="Accenture",
        about=(
            "Accenture is a global Fortune Global 500 professional services company specializing in IT services, "
            "cloud engineering, consulting, and digital transformation across more than 120 countries.\n\n"
            "In campus placements across India, Accenture hires heavily for Associate Software Engineer (ASE) "
            "and Advanced Associate Software Engineer (AASE) roles."
        ),
        role="Associate Software Engineer (ASE / AASE)",
        ctc_total="₹ 4.6 LPA – ₹ 6.5 LPA",
        ctc_items=[
            {"label": "ASE Fixed + Variable", "value": "₹ 4.60 LPA"},
            {"label": "AASE Package", "value": "₹ 6.50 LPA"},
            {"label": "Joining / Relocation Bonus", "value": "As per role"},
        ],
        eligibility=[
            "Minimum 60% or 6.5 CGPA in B.E / B.Tech / MCA.",
            "No active backlogs at the time of assessment.",
            "Maximum 1 year education gap allowed.",
        ],
        recruitment_process=[
            "1. Cognitive & Technical Assessment (90 mins, 90 MCQs)",
            "2. Coding Round (2 Coding Questions — 45 mins)",
            "3. Communication Assessment (Verbal & Listening)",
            "4. Technical + HR Interview",
        ],
        topics_covered=[
            "Critical Reasoning & Problem Solving",
            "Abstract Reasoning & Verbal Ability",
            "Pseudocode & Common Applications (MS Office, Cloud, Security)",
            "Fundamentals of Networking & Cloud",
            "Basic Coding (Arrays, Strings, Math)",
        ],
        important_note=[
            "Conducted on CoCubes / HirePro / Accenture Assessment Platform.",
            "Coding round unlocks only after clearing the Cognitive & Technical cutoff.",
        ],
        exam_style="Accenture Cognitive + Technical MCQs: pseudocode tracing, cloud/networking basics, abstract reasoning, and concise array/string coding logic.",
        sample_questions=[
            {
                "title": "Sample 1: Pseudocode Output Tracing",
                "problem": (
                    "What is the output of the pseudocode:\n"
                    "Integer a = 5, b = 3, c = 2\n"
                    "If ((a & b) > c) then a = a + b Else b = b + c\n"
                    "Print (a + b)"
                ),
                "explanation": "Bitwise AND: 5 (101) & 3 (011) = 1 (001). Since 1 > 2 is false, the Else branch runs: b = 3 + 2 = 5. Output: a + b = 5 + 5 = 10.",
            },
            {
                "title": "Sample 2: Cloud & Networking Fundamentals",
                "problem": "Which cloud service model provides virtualized computing resources (VMs, storage, networks) over the internet?",
                "explanation": "IaaS (Infrastructure as a Service), such as AWS EC2 or Azure VMs, delivers raw compute, storage, and networking.",
            },
            {
                "title": "Sample 3: Coding — Difference of Divisible vs Non-Divisible Sums",
                "problem": "Given n = 4 and m = 20, find `(sum of numbers from 1 to m NOT divisible by n) - (sum of numbers divisible by n)`.",
                "explanation": "Divisible by 4 up to 20: 4+8+12+16+20 = 60. Total sum 1..20 = 210. Non-divisible = 150. Difference = 150 - 60 = 90.",
            },
        ],
    ),
    _make_service_company(
        slug="tcs-nqt",
        name="TCS NQT",
        about=(
            "Tata Consultancy Services (TCS) is India's largest IT services and consulting organization. "
            "The TCS National Qualifier Test (NQT) is a unified national-level hiring exam opening doors to Ninja, Digital, and Prime roles.\n\n"
            "Strong performance in the Advanced Section can upgrade candidates from Ninja to Digital or Prime packages."
        ),
        role="System Engineer (Ninja / Digital / Prime)",
        ctc_total="₹ 3.36 LPA – ₹ 9.0 LPA",
        ctc_items=[
            {"label": "TCS Ninja", "value": "₹ 3.36 LPA"},
            {"label": "TCS Digital", "value": "₹ 7.00 LPA"},
            {"label": "TCS Prime", "value": "₹ 9.00 LPA"},
        ],
        eligibility=[
            "Minimum 60% or 6.0 CGPA throughout 10th, 12th, and Graduation.",
            "Maximum 1 pending backlog allowed (must be cleared before joining).",
            "Education gap not exceeding 24 months.",
        ],
        recruitment_process=[
            "1. TCS NQT Foundation Section (Numerical, Verbal, Reasoning)",
            "2. TCS NQT Advanced Section (Advanced Quant, Reasoning & Coding)",
            "3. Technical, Managerial & HR Interview",
        ],
        topics_covered=[
            "Numerical Ability (Percentages, Time & Work, Mensuration, DI)",
            "Verbal Ability (Reading Comprehension, Cloze Test, Grammar)",
            "Reasoning Ability (Syllogisms, Seating, Data Sufficiency)",
            "Advanced Coding (Arrays, Strings, Number Theory, Dynamic Programming)",
        ],
        important_note=[
            "Conducted on TCS iON platform; strict sectional timers apply.",
            "No negative marking in Foundation and Advanced MCQs.",
        ],
        exam_style="TCS NQT style: quantitative aptitude word problems, data interpretation, logical puzzles, English grammar, and 2 coding problems (easy + medium).",
        sample_questions=[
            {
                "title": "Sample 1: Numerical Ability — Mixture & Ratio",
                "problem": "A 60-litre mixture has milk and water in the ratio 2:1. How much water must be added to make the ratio 1:2?",
                "explanation": "Milk = 40 L, Water = 20 L. For 1:2 ratio, water must be 80 L. Water to add = 80 - 20 = 60 litres.",
            },
            {
                "title": "Sample 2: Reasoning — Letter & Number Analogy",
                "problem": "If 'SYSTEM' is written as 'SYSMET' and 'NEARER' as 'AENRER', how is 'FRACTION' written?",
                "explanation": "Split into two halves and reverse each half: FRAC -> CARF, TION -> NOIT. Result: CARFNOIT.",
            },
            {
                "title": "Sample 3: Coding — Count Subarrays with Given Sum",
                "problem": "Given an integer array `nums` and integer `k`, find the total number of continuous subarrays whose sum equals `k`.",
                "explanation": "Use a prefix sum hash map storing counts of seen prefix sums. At each index, add `map[prefix - k]` to the answer in O(N) time.",
            },
        ],
    ),
    _make_service_company(
        slug="tcs-digital",
        name="TCS Digital",
        about=(
            "TCS Digital is TCS's premium digital-transformation hiring track focused on AI, Cloud, Full-Stack, and Data Engineering.\n\n"
            "Candidates selected for TCS Digital work on next-generation enterprise modernization projects with accelerated career growth."
        ),
        role="Digital Systems Engineer",
        ctc_total="₹ 7.00 LPA",
        ctc_items=[
            {"label": "Base + Allowances", "value": "₹ 6.40 LPA"},
            {"label": "Performance Variable", "value": "₹ 0.60 LPA"},
        ],
        eligibility=[
            "Minimum 60% or 6.0 CGPA in 10th, 12th, and B.E / B.Tech.",
            "No active backlogs at interview time.",
        ],
        recruitment_process=[
            "1. TCS NQT Advanced Quantitative & Coding Test",
            "2. Technical Deep-Dive Interview (DSA + Cloud/SQL)",
            "3. HR & Managerial Interview",
        ],
        topics_covered=[
            "Advanced Quantitative & Probability",
            "Medium-Hard Coding (Strings, Matrix, DP, Greedy)",
            "SQL, DBMS & System Design Basics",
            "Cloud, Python/Java & Modern Web",
        ],
        important_note=["Conducted on TCS iON. Strong performance in both coding questions is key for Digital shortlisting."],
        exam_style="TCS Digital style: tricky probability/combinatorics, medium DSA coding (matrix, DP, greedy), and CS core MCQs.",
        sample_questions=[
            {
                "title": "Sample 1: Unique Paths in a Grid with Obstacles",
                "problem": "Given an M x N grid with obstacles marked as 1, count unique paths from top-left (0,0) to bottom-right (M-1,N-1) moving only right or down.",
                "explanation": "Use 2D DP where `dp[i][j] = 0` if `grid[i][j] == 1`, else `dp[i-1][j] + dp[i][j-1]`. Time O(M*N).",
            },
            {
                "title": "Sample 2: Permutations & Combinatorics",
                "problem": "In how many ways can the letters of the word 'LEADER' be arranged?",
                "explanation": "6 letters with 'E' repeated twice: 6! / 2! = 720 / 2 = 360 ways.",
            },
            {
                "title": "Sample 3: SQL Window / Aggregate Query",
                "problem": "Write an SQL query to find the second highest distinct salary from an `Employees` table.",
                "explanation": "`SELECT MAX(salary) FROM Employees WHERE salary < (SELECT MAX(salary) FROM Employees);`",
            },
        ],
    ),
    _make_service_company(
        slug="tcs-ninja",
        name="TCS Ninja",
        about=(
            "TCS Ninja is TCS's core entry-level engineering track for fresh graduates across B.E, B.Tech, M.E, M.Tech, MCA, and M.Sc.\n\n"
            "It assesses foundational aptitude, programming logic, and core computer science readiness."
        ),
        role="Assistant System Engineer (Trainee)",
        ctc_total="₹ 3.36 LPA – ₹ 3.53 LPA",
        ctc_items=[
            {"label": "UG Package", "value": "₹ 3.36 LPA"},
            {"label": "PG Package", "value": "₹ 3.53 LPA"},
        ],
        eligibility=["60% or 6.0 CGPA in 10th, 12th, Graduation.", "Up to 1 active backlog allowed during test."],
        recruitment_process=["1. NQT Foundation Test", "2. Basic Coding Section", "3. Technical + HR Interview"],
        topics_covered=["Arithmetic & Number System", "Verbal English", "C/Java/Python Output Tracing", "Basic Coding"],
        important_note=["Conducted on TCS iON. Focus on accuracy and speed in Foundation Quant & Verbal."],
        exam_style="TCS Ninja style: foundational arithmetic, verbal grammar, C/Python output MCQs, and basic array/number coding.",
        sample_questions=[
            {
                "title": "Sample 1: Simple & Compound Interest",
                "problem": "Find the difference between Compound Interest and Simple Interest on ₹ 5,000 at 10% p.a. for 2 years.",
                "explanation": "Difference for 2 years = P * (R/100)^2 = 5000 * (0.1)^2 = ₹ 50.",
            },
            {
                "title": "Sample 2: C Pointer Output",
                "problem": "If `int a[] = {10, 20, 30, 40}; int *p = a;`, what does `*(p + 2)` print?",
                "explanation": "Pointer arithmetic advances by 2 ints: `*(p + 2)` equals `a[2]`, which is 30.",
            },
            {
                "title": "Sample 3: Armstrong Number Check",
                "problem": "Check whether 153 is an Armstrong number.",
                "explanation": "1^3 + 5^3 + 3^3 = 1 + 125 + 27 = 153, so yes.",
            },
        ],
    ),
    _make_service_company(
        slug="infosys",
        name="Infosys",
        about=(
            "Infosys is a global leader in next-generation digital services and consulting, headquartered in Bengaluru.\n\n"
            "Infosys recruits freshers for Systems Engineer (SE), Digital Specialist Engineer (DSE), and Specialist Programmer (SP) roles."
        ),
        role="Systems Engineer / Specialist Programmer",
        ctc_total="₹ 3.60 LPA – ₹ 9.50 LPA",
        ctc_items=[
            {"label": "Systems Engineer", "value": "₹ 3.60 LPA"},
            {"label": "Digital Specialist Engineer", "value": "₹ 6.25 LPA"},
            {"label": "Specialist Programmer", "value": "₹ 9.50 LPA"},
        ],
        eligibility=["Minimum 60% in 10th, 12th, and Graduation.", "No active backlogs at onboarding."],
        recruitment_process=[
            "1. Online Test (Reasoning, Math, Verbal, Pseudocode, Puzzle)",
            "2. Technical + HR Interview",
        ],
        topics_covered=[
            "Logical & Analytical Reasoning",
            "Cryptarithmetic & Mathematical Puzzles",
            "Verbal Ability & Reading Comprehension",
            "Pseudocode & Data Structures",
        ],
        important_note=["Infosys is famous for Cryptarithmetic puzzles and Pseudocode tracing in its online test."],
        exam_style="Infosys style: logical puzzles, cryptarithmetic/number puzzles, pseudocode loops, and verbal sentence correction.",
        sample_questions=[
            {
                "title": "Sample 1: Cryptarithmetic Puzzle",
                "problem": "If SEND + MORE = MONEY (each letter is a unique digit 0-9), what is the value of M?",
                "explanation": "Adding two 4-digit numbers to get a 5-digit number forces carry into ten-thousands place: M = 1.",
            },
            {
                "title": "Sample 2: Pseudocode Recursion",
                "problem": "Function f(n): if n <= 1 return n; return f(n-1) + f(n-2). What is f(6)?",
                "explanation": "Fibonacci sequence: f(0)=0, f(1)=1, f(2)=1, f(3)=2, f(4)=3, f(5)=5, f(6)=8.",
            },
            {
                "title": "Sample 3: Data Sufficiency",
                "problem": "Is X > Y? Statement I: X^2 > Y^2. Statement II: X - Y > 0.",
                "explanation": "Statement I fails for negatives (-5)^2 > 2^2. Statement II directly gives X > Y. Only II is sufficient.",
            },
        ],
    ),
    _make_service_company(
        slug="wipro",
        name="Wipro",
        about=(
            "Wipro Limited is a leading global information technology, consulting, and business process services company.\n\n"
            "Its National Talent Hunt (NTH) and Elite programs hire engineering graduates into Project Engineer roles."
        ),
        role="Project Engineer (Elite / Turbo)",
        ctc_total="₹ 3.50 LPA – ₹ 6.50 LPA",
        ctc_items=[
            {"label": "Wipro Elite", "value": "₹ 3.50 LPA"},
            {"label": "Wipro Turbo", "value": "₹ 5.50 – ₹ 6.50 LPA"},
        ],
        eligibility=["60% or 6.0 CGPA in 10th, 12th, and Graduation.", "Max 3 years education gap allowed."],
        recruitment_process=["1. Aptitude, Logical & Verbal", "2. Essay Writing", "3. Coding (2 Questions)", "4. Technical + HR Interview"],
        topics_covered=["Quantitative Aptitude", "Logical Reasoning", "Verbal & Essay Writing", "Basic-Medium Coding"],
        important_note=["Conducted on AMCAT / Superset. Includes a 20-minute written English essay section."],
        exam_style="Wipro Elite/NTH style: AMCAT-style quant, logical reasoning, English grammar, and 2 array/string coding tasks.",
        sample_questions=[
            {
                "title": "Sample 1: Profit & Loss",
                "problem": "By selling an article for ₹ 480, a trader loses 20%. At what price should he sell to gain 20%?",
                "explanation": "CP = 480 / 0.8 = 600. Desired SP = 600 * 1.2 = ₹ 720.",
            },
            {
                "title": "Sample 2: Coding — Second Largest Element",
                "problem": "Find the second largest distinct element in an array in a single pass.",
                "explanation": "Track `first` and `second` initialized to -inf; update both in O(N) time and O(1) space.",
            },
            {
                "title": "Sample 3: Verbal — Error Spotting",
                "problem": "Identify the error: 'Each of the students were given a certificate.'",
                "explanation": "'Each' is singular, so 'were' should be 'was'.",
            },
        ],
    ),
    _make_service_company(
        slug="cognizant-genc",
        name="Cognizant GenC",
        about=(
            "Cognizant is a Fortune 500 multinational IT services and consulting company headquartered in Teaneck, New Jersey, with major delivery centers in India.\n\n"
            "Cognizant hires through GenC, GenC Elevate, and GenC Next tracks."
        ),
        role="Programmer Analyst Trainee (GenC / GenC Next)",
        ctc_total="₹ 4.00 LPA – ₹ 6.75 LPA",
        ctc_items=[
            {"label": "GenC", "value": "₹ 4.00 LPA"},
            {"label": "GenC Elevate", "value": "₹ 4.25 LPA"},
            {"label": "GenC Next", "value": "₹ 6.75 LPA"},
        ],
        eligibility=["Minimum 60% in 10th, 12th, and Graduation.", "No standing arrears."],
        recruitment_process=["1. Aptitude + Automata Fix / SQL + Coding", "2. Communication Assessment", "3. Technical & HR Interview"],
        topics_covered=["Quantitative Aptitude", "Logical Reasoning", "SQL Queries", "Code Debugging (Automata Fix)", "Java/Python Coding"],
        important_note=["Conducted on Mettl / AMCAT. GenC Next includes live coding and SQL queries."],
        exam_style="Cognizant GenC style: SQL query questions, code debugging (Automata Fix), quant, and OOP/Java MCQs.",
        sample_questions=[
            {
                "title": "Sample 1: SQL — Department Employee Count",
                "problem": "Write an SQL query to list departments having more than 5 employees.",
                "explanation": "`SELECT dept_id, COUNT(*) FROM Employees GROUP BY dept_id HAVING COUNT(*) > 5;`",
            },
            {
                "title": "Sample 2: Automata Fix — Off-by-One Bug",
                "problem": "A loop `for (int i = 0; i <= n; i++) sum += arr[i];` crashes on array of size `n`. Fix it.",
                "explanation": "Change `i <= n` to `i < n` because valid indices are `0` to `n - 1`.",
            },
            {
                "title": "Sample 3: Quantitative — Work & Wages",
                "problem": "A and B finish a job in 10 and 15 days respectively. If total wage is ₹ 1,500, what is A's share?",
                "explanation": "Efficiency ratio A:B = 1/10 : 1/15 = 3:2. A's share = (3/5) * 1500 = ₹ 900.",
            },
        ],
    ),
    _make_service_company(
        slug="capgemini",
        name="Capgemini",
        about=(
            "Capgemini is a French multinational IT services and consulting leader with over 340,000 employees worldwide.\n\n"
            "Its campus recruitment tests pseudocode, game-based cognitive ability, and spoken English."
        ),
        role="Analyst / Senior Analyst",
        ctc_total="₹ 4.25 LPA – ₹ 7.50 LPA",
        ctc_items=[
            {"label": "Analyst", "value": "₹ 4.25 LPA"},
            {"label": "Senior Analyst", "value": "₹ 5.75 – ₹ 7.50 LPA"},
        ],
        eligibility=["60% in 10th, 12th, and Graduation.", "No active backlogs."],
        recruitment_process=["1. Technical Pseudocode & DBMS/Cloud MCQ", "2. English Communication", "3. Game-Based Aptitude", "4. Behavioral + Tech Interview"],
        topics_covered=["Pseudocode (Bitwise, Recursion, Loops)", "Data Structures & DBMS", "English Grammar", "Game-Based Cognitive Logic"],
        important_note=["Conducted on CoCubes / Superset. Each round is an elimination round."],
        exam_style="Capgemini style: tricky bitwise/loop pseudocode questions, DBMS/networking MCQs, and English comprehension.",
        sample_questions=[
            {
                "title": "Sample 1: Bitwise XOR Pseudocode",
                "problem": "Compute `p = 6, q = 4; p = p ^ q; q = p ^ q; p = p ^ q;` — what are final p and q?",
                "explanation": "Classic XOR swap: p becomes 4 and q becomes 6.",
            },
            {
                "title": "Sample 2: DBMS — Foreign Key",
                "problem": "Which constraint ensures referential integrity between two relational tables?",
                "explanation": "A Foreign Key ensures every non-null value references an existing Primary/Unique key in the parent table.",
            },
            {
                "title": "Sample 3: English — Active to Passive",
                "problem": "Convert to passive: 'The team deployed the microservice.'",
                "explanation": "'The microservice was deployed by the team.'",
            },
        ],
    ),
    _make_service_company(
        slug="deloitte",
        name="Deloitte",
        about=(
            "Deloitte is one of the Big Four accounting and technology consulting firms, hiring engineering graduates "
            "into Deloitte USI (Advisory & Consulting) and Deloitte India.\n\n"
            "Roles include Associate Analyst and Analyst in Cloud, Cyber, and Software Engineering."
        ),
        role="Analyst / Associate Analyst (USI)",
        ctc_total="₹ 6.50 LPA – ₹ 7.60 LPA",
        ctc_items=[
            {"label": "Base Pay", "value": "₹ 6.00 LPA"},
            {"label": "Joining / Variable Bonus", "value": "₹ 0.50 – ₹ 1.60 LPA"},
        ],
        eligibility=["Minimum 60% or 6.5 CGPA in Graduation.", "No active backlogs."],
        recruitment_process=["1. Online Aptitude + Technical Test (AMCAT)", "2. JAM / Group Case Discussion", "3. Technical + HR Interview"],
        topics_covered=["Quantitative & Logical Reasoning", "Verbal Ability", "SQL, OOP & SDLC", "Case Study & Communication"],
        important_note=["Deloitte places strong emphasis on structured communication and business-case thinking."],
        exam_style="Deloitte style: business-oriented data interpretation, verbal reasoning, SQL/SDLC technical MCQs, and case judgment.",
        sample_questions=[
            {
                "title": "Sample 1: Data Interpretation — Growth Rate",
                "problem": "Company revenue grew from ₹ 240 Cr to ₹ 300 Cr. What is the percentage increase?",
                "explanation": "Increase = (60 / 240) * 100 = 25%.",
            },
            {
                "title": "Sample 2: SDLC & Agile",
                "problem": "In Scrum, who is responsible for prioritizing the Product Backlog?",
                "explanation": "The Product Owner owns and prioritizes the Product Backlog based on business value.",
            },
            {
                "title": "Sample 3: SQL — Duplicate Detection",
                "problem": "Find emails that appear more than once in a `Users` table.",
                "explanation": "`SELECT email FROM Users GROUP BY email HAVING COUNT(*) > 1;`",
            },
        ],
    ),
    _make_service_company(
        slug="amazon",
        name="Amazon",
        about=(
            "Amazon is a global technology leader in e-commerce, cloud computing (AWS), and AI.\n\n"
            "Its SDE-1 hiring process evaluates strong problem-solving in Data Structures & Algorithms along with Amazon's 16 Leadership Principles."
        ),
        role="Software Development Engineer I (SDE-1)",
        ctc_total="₹ 44 LPA – ₹ 46 LPA",
        ctc_items=[
            {"label": "Base Pay", "value": "₹ 19.0 LPA"},
            {"label": "Sign-on Bonus (Yr 1 + Yr 2)", "value": "₹ 15.5 Lakhs"},
            {"label": "RSUs (4-year vest)", "value": "₹ 12+ Lakhs"},
        ],
        eligibility=["B.E / B.Tech in CS/IT/ECE or related fields.", "Strong DSA & CS fundamentals."],
        recruitment_process=["1. Online Assessment (2 Coding + Work Style Survey)", "2. Technical Interviews (2–3 Rounds)", "3. Bar Raiser + Leadership Principles"],
        topics_covered=["Trees, Graphs & Heaps", "Dynamic Programming & Greedy", "Sliding Window & Two Pointers", "OS, DBMS & Amazon Leadership Principles"],
        important_note=["Conducted on HackerRank / Mettl. Every interview round includes behavioral questions on Leadership Principles."],
        exam_style="Amazon SDE-1 style: medium-hard DSA coding (graphs, trees, heaps, sliding window, DP), time complexity, and Leadership Principle behavioral scenarios.",
        sample_questions=[
            {
                "title": "Question 1: K Closest Points to Origin",
                "problem": "Given an array of points `[x, y]` and integer `k`, return the `k` closest points to `(0, 0)`.",
                "explanation": "Maintain a Max-Heap of size `k` keyed by squared distance `x^2 + y^2`, or use Quickselect for O(N) average time.",
                "solutions": {
                    "python": """import heapq
def k_closest(points, k):
    return heapq.nsmallest(k, points, key=lambda p: p[0]*p[0] + p[1]*p[1])""",
                    "cpp": """// Use priority_queue<pair<int, int>> of size k; pop when size > k.""",
                    "java": """// PriorityQueue<int[]> maxHeap sorted by (b[0]*b[0]+b[1]*b[1]) - (a[0]*a[0]+a[1]*a[1]).""",
                },
            },
            {
                "title": "Question 2: Number of Islands (BFS/DFS)",
                "problem": "Given a 2D binary grid of `'1'`s (land) and `'0'`s (water), count the number of islands.",
                "explanation": "Iterate over every cell; whenever `'1'` is found, increment count and run DFS/BFS to mark connected `'1'`s as visited.",
            },
            {
                "title": "Question 3: Leadership Principle — Customer Obsession",
                "problem": "How should you handle a feature request that benefits internal metrics but degrades customer latency?",
                "explanation": "Prioritize customer experience (Customer Obsession), measure latency impact, and optimize before shipping.",
            },
        ],
    ),
    _make_service_company(
        slug="microsoft",
        name="Microsoft",
        about=(
            "Microsoft develops world-leading software, cloud services (Azure), and AI platforms.\n\n"
            "Campus hires for SWE roles are tested on clean algorithmic thinking, edge-case handling, and system design basics."
        ),
        role="Software Engineer (SWE)",
        ctc_total="₹ 45 LPA – ₹ 51 LPA",
        ctc_items=[
            {"label": "Base Pay", "value": "₹ 16 – ₹ 18 LPA"},
            {"label": "Joining Bonus", "value": "₹ 5 Lakhs"},
            {"label": "Stock Award (RSUs)", "value": "₹ 25+ Lakhs"},
        ],
        eligibility=["B.E / B.Tech (CSE/IT/ECE), CGPA >= 7.0/7.5.", "No active backlogs."],
        recruitment_process=["1. Codility Online Coding Test (2–3 Problems)", "2. Technical Interviews (2–3 Rounds)", "3. AA (As Appropriate) / Hiring Manager Round"],
        topics_covered=["Linked Lists, Trees & Graphs", "Recursion & Backtracking", "Dynamic Programming", "System Design & OOPS"],
        important_note=["Conducted on Codility. Edge cases and clean code readability matter heavily."],
        exam_style="Microsoft Codility style: trees/graphs, string manipulation, backtracking, OOPS design, and concurrency MCQs.",
        sample_questions=[
            {
                "title": "Question 1: Lowest Common Ancestor of a Binary Tree",
                "problem": "Given a binary tree and two nodes `p` and `q`, find their Lowest Common Ancestor (LCA).",
                "explanation": "Recurse left and right: if current node is `p` or `q`, return it. If both subtrees return non-null, current node is LCA.",
                "solutions": {
                    "python": """def lca(root, p, q):
    if not root or root == p or root == q:
        return root
    left = lca(root.left, p, q)
    right = lca(root.right, p, q)
    return root if left and right else (left or right)""",
                    "cpp": """TreeNode* lca(TreeNode* root, TreeNode* p, TreeNode* q) {
    if (!root || root == p || root == q) return root;
    auto l = lca(root->left, p, q), r = lca(root->right, p, q);
    return (l && r) ? root : (l ? l : r);
}""",
                    "java": """// Same O(N) post-order traversal returning non-null branch or root.""",
                },
            },
            {
                "title": "Question 2: Merge Intervals",
                "problem": "Given an array of intervals `[start, end]`, merge all overlapping intervals.",
                "explanation": "Sort intervals by `start`. Iterate and merge if `curr.start <= prev.end` by updating `prev.end = max(prev.end, curr.end)`.",
            },
            {
                "title": "Question 3: OS — Mutex vs Semaphore",
                "problem": "What is the key ownership difference between a Mutex and a Binary Semaphore?",
                "explanation": "A Mutex has thread ownership (only the locking thread can unlock it), whereas a Semaphore is a signaling mechanism any thread can signal.",
            },
        ],
    ),
    _make_service_company(
        slug="juspay",
        name="Juspay",
        about=(
            "Juspay is a leading Indian fintech company powering mobile payments infrastructure for major apps and banks.\n\n"
            "Juspay is renowned for its challenging graph-theory online rounds and hackathon-style technical interviews."
        ),
        role="Software Development Engineer (SDE)",
        ctc_total="₹ 21 LPA – ₹ 27 LPA",
        ctc_items=[
            {"label": "Base Pay", "value": "₹ 18 – ₹ 21 LPA"},
            {"label": "ESOPs / Bonus", "value": "₹ 3 – ₹ 6 Lakhs"},
        ],
        eligibility=["Open to B.E / B.Tech with strong algorithmic problem-solving skills."],
        recruitment_process=["1. Online Coding Round (Graphs & Trees)", "2. Hackathon / Pair Programming Round", "3. System & Culture Interview"],
        topics_covered=["Directed Graphs & Cycle Detection", "Shortest Path (BFS / Dijkstra)", "N-ary Trees & Locking", "Functional Programming"],
        important_note=["Expect 3 graph-heavy coding problems in 90 minutes."],
        exam_style="Juspay style: directed graphs, reachability, cycle detection, nearest meeting cell, and tree-locking concurrency problems.",
        sample_questions=[
            {
                "title": "Question 1: Nearest Meeting Cell in Functional Graph",
                "problem": "Given `N` cells where cell `i` points to `edge[i]` (at most 1 outgoing edge), find the nearest node reachable from both `c1` and `c2`.",
                "explanation": "Compute distance arrays `dist1[]` from `c1` and `dist2[]` from `c2` using simple traversal; pick the node minimizing `max(dist1[i], dist2[i])`.",
            },
            {
                "title": "Question 2: Largest Sum Cycle",
                "problem": "In a functional directed graph where each node has at most one outgoing edge, find the maximum sum of node indices in any cycle.",
                "explanation": "Use 3-state DFS (unvisited, visiting, visited) with path prefix sums to compute cycle sums in O(N).",
            },
            {
                "title": "Question 3: Thread-Safe Tree of Space",
                "problem": "How do you check if any ancestor or descendant of a node in an M-ary tree is locked in O(log_M N) time?",
                "explanation": "Maintain `lockedDescendantCount` on ancestors while walking up to the root; check ancestors upward in O(height).",
            },
        ],
    ),
    _make_service_company(
        slug="zscaler",
        name="Zscaler",
        about=(
            "Zscaler is a global cloud security leader providing Zero Trust Exchange services to enterprises worldwide.\n\n"
            "Zscaler hires SWEs with strong foundations in C/C++, Computer Networks, Linux, and DSA."
        ),
        role="Software Engineer (Cloud Security)",
        ctc_total="₹ 22 LPA – ₹ 28 LPA",
        ctc_items=[{"label": "Base Pay", "value": "₹ 16 – ₹ 19 LPA"}, {"label": "RSUs + Bonus", "value": "₹ 6 – ₹ 9 Lakhs"}],
        eligibility=["70% or 7.0 CGPA in B.E / B.Tech (CSE/IT/ECE).", "No active backlogs."],
        recruitment_process=["1. HackerRank Coding + Networking MCQs", "2. Technical Interviews (2 Rounds)", "3. Director / HR Round"],
        topics_covered=["Computer Networks (TCP/IP, TLS, DNS, HTTP)", "C/C++ Pointers & Memory", "Data Structures & Algorithms", "Operating Systems"],
        important_note=["Strong weightage on Computer Networks & C/Linux alongside coding."],
        exam_style="Zscaler style: TCP/IP, TLS handshake, HTTP proxies, C memory/pointers, and medium DSA coding.",
        sample_questions=[
            {
                "title": "Sample 1: Networking — TLS Handshake",
                "problem": "What is the role of the asymmetric key exchange during a TLS handshake?",
                "explanation": "Asymmetric cryptography authenticates the server and securely establishes a shared symmetric session key for fast encrypted data transfer.",
            },
            {
                "title": "Sample 2: C Memory — Dangling Pointer",
                "problem": "What happens if you dereference a pointer after calling `free(ptr)` without setting `ptr = NULL`?",
                "explanation": "It causes undefined behavior (dangling pointer / use-after-free vulnerability).",
            },
            {
                "title": "Sample 3: Coding — Valid IPv4 Address",
                "problem": "Validate whether a string is a valid IPv4 address (4 dot-separated octets in 0..255 with no leading zeros).",
                "explanation": "Split by `.`, check length == 4, digits only, no leading zero if len > 1, and `0 <= int(part) <= 255`.",
            },
        ],
    ),
    _make_service_company(
        slug="thoughtworks",
        name="Thoughtworks",
        about=(
            "Thoughtworks is a global technology consultancy known for agile software engineering, clean code, TDD, and distributed systems.\n\n"
            "Their hiring process uniquely emphasizes pair programming and object-oriented design."
        ),
        role="Application Developer",
        ctc_total="₹ 10.5 LPA – ₹ 11.5 LPA",
        ctc_items=[{"label": "Base + Variable", "value": "₹ 10.5 – ₹ 11.5 LPA"}],
        eligibility=["B.E / B.Tech / MCA, no strict percentage cutoff on skills-first drives."],
        recruitment_process=["1. Code Pairing / Home Assignment", "2. Technical Pair Programming", "3. Social Change & Leadership Round"],
        topics_covered=["Clean OOP Design & SOLID", "Test-Driven Development (TDD)", "Refactoring & Edge Cases", "Agile Practices"],
        important_note=["Thoughtworks evaluates code modularity, naming, unit tests, and collaborative pairing."],
        exam_style="Thoughtworks style: OOP design, SOLID principles, TDD/unit testing, refactoring smells, and clean domain modeling.",
        sample_questions=[
            {
                "title": "Sample 1: SOLID — Open/Closed Principle",
                "problem": "How do you add a new payment method without modifying existing `PaymentProcessor` if-else branches?",
                "explanation": "Define a `PaymentStrategy` interface and inject concrete strategy classes (Open for extension, closed for modification).",
            },
            {
                "title": "Sample 2: TDD Cycle",
                "problem": "What are the three phases of Test-Driven Development (TDD)?",
                "explanation": "Red (write a failing test) -> Green (write minimal code to pass) -> Refactor (clean up while keeping tests green).",
            },
            {
                "title": "Sample 3: Domain Modeling — Parking Lot",
                "problem": "Which classes would you model for a multi-floor Parking Lot system?",
                "explanation": "`ParkingLot`, `Floor`, `ParkingSpot` (Compact/Large/EV), `Ticket`, `Vehicle`, and `PricingStrategy`.",
            },
        ],
    ),
    _make_service_company(
        slug="hcl",
        name="HCLTech",
        about=(
            "HCLTech is a global technology company headquartered in Noida, delivering digital, engineering, and cloud services.\n\n"
            "HCLTech hires freshers as Graduate Engineer Trainees (GET) across software and infrastructure tracks."
        ),
        role="Graduate Engineer Trainee (GET)",
        ctc_total="₹ 3.65 LPA – ₹ 4.25 LPA",
        ctc_items=[{"label": "Fixed CTC", "value": "₹ 3.65 – ₹ 4.25 LPA"}],
        eligibility=["Minimum 60% or 65% in 10th, 12th, and Graduation.", "No active backlogs."],
        recruitment_process=["1. Online Aptitude + Technical + Coding", "2. Technical Interview", "3. HR Interview"],
        topics_covered=["Quantitative Aptitude", "Logical Reasoning", "Verbal English", "C/Java/SQL Basics"],
        important_note=["Conducted on Mettl / FirstNaukri."],
        exam_style="HCLTech style: standard quant, logical reasoning, C/Java/SQL basics, and simple coding.",
        sample_questions=[
            {
                "title": "Sample 1: Ratio & Proportion",
                "problem": "If A:B = 2:3 and B:C = 4:5, find A:B:C.",
                "explanation": "Scale B to 12: A:B = 8:12 and B:C = 12:15 -> A:B:C = 8:12:15.",
            },
            {
                "title": "Sample 2: SQL — Primary vs Unique Key",
                "problem": "Can a UNIQUE key column contain NULL values in standard SQL?",
                "explanation": "Yes, a UNIQUE column allows NULL(s), whereas a PRIMARY KEY cannot contain NULL.",
            },
            {
                "title": "Sample 3: Coding — Reverse Words",
                "problem": "Reverse the order of words in `'hello placement hub'`.",
                "explanation": "Split by whitespace and reverse list -> `'hub placement hello'`.",
            },
        ],
    ),
    _make_service_company(
        slug="ibm",
        name="IBM",
        about=(
            "IBM is a global technology and hybrid-cloud pioneer operating in over 175 countries.\n\n"
            "IBM India hires freshers for Associate System Engineer and Software Developer roles."
        ),
        role="Associate System Engineer",
        ctc_total="₹ 4.50 LPA – ₹ 11.0 LPA",
        ctc_items=[{"label": "ASE", "value": "₹ 4.50 LPA"}, {"label": "ISL / Research", "value": "₹ 9 – ₹ 11 LPA"}],
        eligibility=["60% or 6.0 CGPA in Graduation.", "No active backlogs."],
        recruitment_process=["1. Cognitive Ability Assessment (Games)", "2. Coding & English Test", "3. Technical + HR Interview"],
        topics_covered=["Number Series & Cognitive Puzzles", "Coding (Strings, Arrays)", "English Assessment", "Linux, Cloud & OOP"],
        important_note=["IBM uses HackerRank for coding and Kenexa cognitive games."],
        exam_style="IBM style: cognitive number/pattern games, HackerRank string/array coding, Linux/Cloud/OOP MCQs.",
        sample_questions=[
            {
                "title": "Sample 1: Number Series",
                "problem": "Find the missing term: 2, 6, 12, 20, 30, ?",
                "explanation": "Differences are +4, +6, +8, +10, +12 -> 30 + 12 = 42 (n*(n+1)).",
            },
            {
                "title": "Sample 2: Linux Permissions",
                "problem": "What does `chmod 755 script.sh` grant?",
                "explanation": "Owner: rwx (7), Group: r-x (5), Others: r-x (5).",
            },
            {
                "title": "Sample 3: Coding — FizzBuzz / String Compression",
                "problem": "Compress `'aaabbc'` into `'a3b2c1'`.",
                "explanation": "Single linear scan counting consecutive identical characters in O(N).",
            },
        ],
    ),
    _make_service_company(
        slug="tech-mahindra",
        name="Tech Mahindra",
        about=(
            "Tech Mahindra is a leading Indian multinational IT and telecom solutions provider part of the Mahindra Group.\n\n"
            "It recruits engineering graduates into Associate Software Engineer roles."
        ),
        role="Associate Software Engineer",
        ctc_total="₹ 3.25 LPA – ₹ 5.50 LPA",
        ctc_items=[{"label": "Regular", "value": "₹ 3.25 LPA"}, {"label": "Supercoder", "value": "₹ 5.50 LPA"}],
        eligibility=["60% in 10th, 12th, and Graduation.", "No active backlogs."],
        recruitment_process=["1. Aptitude + English + Essay", "2. Technical + Psychometric + Coding", "3. Technical & HR Interview"],
        topics_covered=["Quantitative & Logical Reasoning", "English Grammar & Essay", "CS Fundamentals", "Basic Coding"],
        important_note=["Conducted on Mettl. Psychometric round is non-eliminative but used in HR."],
        exam_style="Tech Mahindra style: quant, logical reasoning, English essay/grammar, and C/Java output MCQs.",
        sample_questions=[
            {
                "title": "Sample 1: Averages",
                "problem": "The average of 5 numbers is 20. If one number is excluded, the average becomes 18. Find the excluded number.",
                "explanation": "Total of 5 = 100; total of 4 = 72; excluded = 100 - 72 = 28.",
            },
            {
                "title": "Sample 2: Java — String Immutability",
                "problem": "Why is `String` immutable in Java?",
                "explanation": "For String Pool caching, thread safety, and security (classloading/URLs/keys).",
            },
            {
                "title": "Sample 3: Coding — Palindrome Check",
                "problem": "Check if a string is a palindrome ignoring case.",
                "explanation": "Compare `s[left].lower()` and `s[right].lower()` using two pointers converging to the center.",
            },
        ],
    ),
    _make_service_company(
        slug="ltimindtree",
        name="LTIMindtree",
        about=(
            "LTIMindtree is a global technology consulting and digital solutions company formed by the merger of L&T Infotech and Mindtree.\n\n"
            "It hires freshers into Graduate Engineer Trainee roles across enterprise cloud and data."
        ),
        role="Graduate Engineer Trainee",
        ctc_total="₹ 4.05 LPA – ₹ 5.05 LPA",
        ctc_items=[{"label": "GET Base", "value": "₹ 4.05 LPA"}, {"label": "Role Bonus", "value": "Up to ₹ 1.0 LPA"}],
        eligibility=["60% in 10th, 12th, Graduation.", "No active backlogs."],
        recruitment_process=["1. Aptitude + Technical + Coding", "2. Technical Interview", "3. HR Interview"],
        topics_covered=["Aptitude & Reasoning", "OOP, DBMS, OS", "1–2 Coding Questions"],
        important_note=["Conducted on Mettl / Berke."],
        exam_style="LTIMindtree style: aptitude, OOP/DBMS MCQs, and practical array/string coding.",
        sample_questions=[
            {
                "title": "Sample 1: Speed & Distance",
                "problem": "A car covers 150 km at 50 km/hr and returns at 75 km/hr. Find the average speed.",
                "explanation": "Harmonic mean: 2*50*75 / (50+75) = 7500 / 125 = 60 km/hr.",
            },
            {
                "title": "Sample 2: DBMS — Truncate vs Delete",
                "problem": "Which command is DDL, faster, and cannot be rolled back in most SQL engines without transaction support?",
                "explanation": "TRUNCATE is a DDL command that deallocates data pages, whereas DELETE is DML and logs row deletions.",
            },
            {
                "title": "Sample 3: Coding — Move Zeroes to End",
                "problem": "Move all zeroes in an array to the end while preserving relative order of non-zero elements.",
                "explanation": "Maintain a write index `j = 0`; copy non-zero elements to `arr[j++]`, then fill remaining indices with 0.",
            },
        ],
    ),
    _make_service_company(
        slug="epam",
        name="EPAM Systems",
        about=(
            "EPAM Systems is a global software engineering and digital platform services leader.\n\n"
            "EPAM's campus test focuses heavily on clean Java/Python/C# coding and OOP fundamentals."
        ),
        role="Junior Software Engineer",
        ctc_total="₹ 6.00 LPA – ₹ 8.00 LPA",
        ctc_items=[{"label": "Fixed CTC", "value": "₹ 6.00 – ₹ 8.00 LPA"}],
        eligibility=["Minimum 60% in 10th, 12th, and B.Tech.", "No active backlogs."],
        recruitment_process=["1. Online Coding & Technical MCQs", "2. Technical Round 1", "3. Technical Round 2 + HR"],
        topics_covered=["Java / Python / C# Core", "Data Structures & Algorithms", "OOP & Design Patterns", "SQL"],
        important_note=["EPAM emphasizes clean, well-structured OOP code and unit-test awareness."],
        exam_style="EPAM style: Java/OOP/Collections MCQs, clean DSA coding, and SQL.",
        sample_questions=[
            {
                "title": "Sample 1: Java Collections",
                "problem": "What is the time complexity of `HashMap.get()` in Java 8+ in average vs worst case?",
                "explanation": "O(1) average; O(log N) worst case when a bucket converts from a linked list to a balanced Red-Black Tree.",
            },
            {
                "title": "Sample 2: Coding — Anagram Grouping",
                "problem": "Group a list of strings into anagrams.",
                "explanation": "Use a hash map keyed by sorted string or 26-letter frequency tuple.",
            },
            {
                "title": "Sample 3: OOP — Interface vs Abstract Class",
                "problem": "When should you prefer an interface over an abstract class?",
                "explanation": "When defining a capability contract across unrelated classes (supports multiple inheritance of type).",
            },
        ],
    ),
    _make_service_company(
        slug="hexaware",
        name="Hexaware",
        about="Hexaware Technologies is a global IT & BPO services company focused on cloud, automation, and digital transformation.",
        role="Graduate Engineer Trainee (GET)",
        ctc_total="₹ 4.00 LPA – ₹ 6.00 LPA",
        ctc_items=[{"label": "GET Package", "value": "₹ 4.00 LPA"}, {"label": "PGET", "value": "₹ 6.00 LPA"}],
        eligibility=["60% in 10th, 12th, Graduation.", "No active backlogs."],
        recruitment_process=["1. Aptitude + Domain Test", "2. Coding + Communication", "3. Technical & HR Interview"],
        topics_covered=["Quantitative Aptitude", "Logical Reasoning", "Pseudocode", "C/Java Basics"],
        important_note=["Conducted on Superset / Mettl."],
        exam_style="Hexaware style: aptitude, pseudocode, communication, and basic coding MCQs.",
        sample_questions=[
            {"title": "Sample 1: Partnership", "problem": "A invests ₹ 4,000 for 6 months and B invests ₹ 6,000 for 4 months. Find profit ratio.", "explanation": "(4000*6) : (6000*4) = 24000 : 24000 = 1:1."},
            {"title": "Sample 2: Coding — Prime Check", "problem": "What is the optimal upper bound for trial division when checking if N is prime?", "explanation": "Up to sqrt(N), since any composite N has at least one factor <= sqrt(N)."},
            {"title": "Sample 3: OS — Context Switch", "problem": "Which structure stores a process's state during a context switch?", "explanation": "Process Control Block (PCB)."},
        ],
    ),
    _make_service_company(
        slug="dxc",
        name="DXC Technology",
        about="DXC Technology is a Fortune 500 global IT services company helping enterprises run mission-critical systems.",
        role="Associate Professional Software Engineer",
        ctc_total="₹ 4.00 LPA – ₹ 4.20 LPA",
        ctc_items=[{"label": "Fixed CTC", "value": "₹ 4.00 – ₹ 4.20 LPA"}],
        eligibility=["60% in 10th, 12th, Graduation.", "No active backlogs."],
        recruitment_process=["1. Aptitude + Logical + Essay + Automata Fix", "2. Technical + HR Interview"],
        topics_covered=["Quant & Reasoning", "English & Essay", "Code Debugging (Automata Fix)", "CS Fundamentals"],
        important_note=["Conducted on AMCAT."],
        exam_style="DXC AMCAT style: quant, logical reasoning, English grammar, and Automata debugging.",
        sample_questions=[
            {"title": "Sample 1: Probability", "problem": "A card is drawn from a 52-card deck. Probability of getting a King or Heart?", "explanation": "(4 + 13 - 1) / 52 = 16 / 52 = 4 / 13."},
            {"title": "Sample 2: Debugging — Infinite Loop", "problem": "Why does `while (n > 0) { sum += n; }` loop forever?", "explanation": "`n` is never decremented inside the loop body."},
            {"title": "Sample 3: Networking — ARP", "problem": "Which protocol maps an IPv4 address to a MAC address?", "explanation": "ARP (Address Resolution Protocol)."},
        ],
    ),
    _make_service_company(
        slug="pwc",
        name="PwC",
        about="PricewaterhouseCoopers (PwC) is a Big Four consulting and assurance network hiring engineering graduates into Tech Consulting & Cyber.",
        role="Associate / Tech Consultant",
        ctc_total="₹ 6.00 LPA – ₹ 7.50 LPA",
        ctc_items=[{"label": "Fixed CTC", "value": "₹ 6.00 LPA"}, {"label": "Bonus", "value": "Up to ₹ 1.5 LPA"}],
        eligibility=["60% or 6.0 CGPA throughout.", "No active backlogs."],
        recruitment_process=["1. Aptitude + Technical MCQ", "2. Technical Interview", "3. Partner / HR Interview"],
        topics_covered=["Quantitative & DI", "Logical Reasoning", "SQL & Cloud Basics", "Consulting Case Judgment"],
        important_note=["Strong analytical clarity and client-communication skills are evaluated."],
        exam_style="PwC style: data interpretation, logical puzzles, SQL/cloud MCQs, and consulting scenarios.",
        sample_questions=[
            {"title": "Sample 1: Data Interpretation", "problem": "If a product's cost is ₹ 800 and overhead is 25% of cost, what is the total cost?", "explanation": "800 + 0.25*800 = ₹ 1,000."},
            {"title": "Sample 2: SQL — NULL Handling", "problem": "Which SQL function replaces NULL with a default value?", "explanation": "`COALESCE(col, default_val)` (or `IFNULL` / `NVL`)."},
            {"title": "Sample 3: Cybersecurity", "problem": "What does MFA stand for and why is it critical?", "explanation": "Multi-Factor Authentication requires 2+ independent verification factors, blocking password-only breaches."},
        ],
    ),
    _make_service_company(
        slug="ey",
        name="EY",
        about="Ernst & Young (EY) is a Big Four professional services firm hiring engineering graduates into Technology Consulting and GDS.",
        role="Associate Software Engineer / Tech Risk",
        ctc_total="₹ 5.50 LPA – ₹ 6.80 LPA",
        ctc_items=[{"label": "Fixed CTC", "value": "₹ 5.50 – ₹ 6.80 LPA"}],
        eligibility=["60% in 10th, 12th, Graduation.", "No standing arrears."],
        recruitment_process=["1. Aptitude & Technical Assessment", "2. Technical Interview", "3. HR Interview"],
        topics_covered=["Quant & Reasoning", "Verbal Ability", "SQL, Python & SDLC", "Cybersecurity Basics"],
        important_note=["Conducted on HirePro / SHL."],
        exam_style="EY style: SHL numerical/verbal reasoning, SQL/Python fundamentals, and risk/SDLC scenarios.",
        sample_questions=[
            {"title": "Sample 1: Compound Growth", "problem": "A team's output grows 10% in Q1 and 10% in Q2. Net growth?", "explanation": "1.10 * 1.10 - 1 = 21%."},
            {"title": "Sample 2: Python — List vs Tuple", "problem": "What is the key difference between a Python `list` and `tuple`?", "explanation": "Lists are mutable (`[]`), whereas tuples are immutable (`()`) and hashable if elements are hashable."},
            {"title": "Sample 3: SDLC — Regression Testing", "problem": "Why is regression testing performed?", "explanation": "To verify that new changes have not broken existing functionality."},
        ],
    ),
    _make_service_company(
        slug="zs-associates",
        name="ZS Associates",
        about="ZS Associates is a global management consulting and technology firm specializing in healthcare analytics and AI.",
        role="Business Technology Solutions Associate (BTSA)",
        ctc_total="₹ 12.5 LPA – ₹ 13.65 LPA",
        ctc_items=[{"label": "Base Pay", "value": "₹ 9.50 LPA"}, {"label": "Bonus + Benefits", "value": "₹ 3.0 – ₹ 4.15 LPA"}],
        eligibility=["65% or 6.5 CGPA in B.E / B.Tech.", "No active backlogs."],
        recruitment_process=["1. Online Aptitude + Caselet + SQL/Tech", "2. Case Study Round", "3. Behavioral + Tech Interview"],
        topics_covered=["Data Interpretation & Guesstimates", "SQL & Data Modeling", "Logical Puzzles", "Business Case Studies"],
        important_note=["ZS is known for structured case interviews and SQL/data-analytics questions."],
        exam_style="ZS Associates style: business DI, guesstimates, SQL joins/aggregations, and analytical puzzles.",
        sample_questions=[
            {"title": "Sample 1: SQL — Top 3 Customers by Spend", "problem": "Write SQL to get top 3 `customer_id`s by total `amount` in `Orders`.", "explanation": "`SELECT customer_id, SUM(amount) AS total FROM Orders GROUP BY customer_id ORDER BY total DESC LIMIT 3;`"},
            {"title": "Sample 2: Business DI", "problem": "Market size is 10M units, firm share rises from 12% to 15%. How many new units?", "explanation": "3% of 10M = 300,000 units."},
            {"title": "Sample 3: Puzzle — 8 Balls", "problem": "Minimum weighings on a balance scale to find 1 heavier ball among 8?", "explanation": "2 weighings (split 3-3-2)."},
        ],
    ),
    _make_service_company(
        slug="musigma",
        name="Mu Sigma",
        about="Mu Sigma is one of the world's largest pure-play big data analytics and decision sciences companies.",
        role="Trainee Decision Scientist",
        ctc_total="₹ 5.00 LPA – ₹ 6.00 LPA (multi-year progression)",
        ctc_items=[{"label": "Year 1 Package", "value": "₹ 5.00 LPA"}],
        eligibility=["60% throughout academics.", "Strong analytical & math aptitude."],
        recruitment_process=["1. MuApt (Aptitude + Puzzles + Coding)", "2. Video Synthesis / Case GD", "3. Final Interview"],
        topics_covered=["Probability & Statistics", "Logical Puzzles", "SQL & Python/R Basics", "Business Case Synthesis"],
        important_note=["MuApt tests rapid decision-making, statistics, and lateral-thinking puzzles."],
        exam_style="Mu Sigma style: probability, statistics, lateral-thinking puzzles, and basic SQL/Python.",
        sample_questions=[
            {"title": "Sample 1: Bayes / Conditional Probability", "problem": "A fair coin is tossed twice. Given at least one is Heads, probability both are Heads?", "explanation": "Sample space {HH, HT, TH} -> 1/3."},
            {"title": "Sample 2: Mean vs Median", "problem": "Which measure of central tendency is more robust to extreme outliers?", "explanation": "Median, because it depends only on the middle rank rather than magnitude."},
            {"title": "Sample 3: SQL — NULL Count", "problem": "Does `COUNT(col)` include NULL values?", "explanation": "No, `COUNT(col)` ignores NULLs whereas `COUNT(*)` counts all rows."},
        ],
    ),
    _make_service_company(
        slug="nagarro",
        name="Nagarro",
        about="Nagarro is a global digital engineering leader specializing in agile product engineering and cloud modernization.",
        role="Associate Software Engineer",
        ctc_total="₹ 4.50 LPA – ₹ 6.50 LPA",
        ctc_items=[{"label": "Fixed CTC", "value": "₹ 4.50 – ₹ 6.50 LPA"}],
        eligibility=["60% in B.E / B.Tech / MCA.", "No active backlogs."],
        recruitment_process=["1. Online Aptitude + 3 Coding Questions", "2. Technical Interview", "3. HR Round"],
        topics_covered=["Strings & Arrays", "Recursion & Hashing", "OOP & DBMS"],
        important_note=["Coding round typically has 3 problems of increasing difficulty on Mettl."],
        exam_style="Nagarro style: practical string/array coding, hashing, recursion, and OOP/DBMS MCQs.",
        sample_questions=[
            {"title": "Sample 1: First Non-Repeating Character", "problem": "Find the first non-repeating character in `'swiss'`.", "explanation": "Count frequencies in pass 1, return `'w'` in pass 2."},
            {"title": "Sample 2: Array Rotation", "problem": "Rotate an array right by `k` steps in O(1) extra space.", "explanation": "Reverse whole array, reverse first `k`, reverse remaining `n-k`."},
            {"title": "Sample 3: OOP — Polymorphism", "problem": "Compile-time vs Runtime polymorphism in Java/C++?", "explanation": "Overloading is compile-time; overriding via virtual dispatch is runtime."},
        ],
    ),
    _make_service_company(
        slug="kpit",
        name="KPIT",
        about="KPIT Technologies is a global automotive software engineering partner specializing in embedded systems, EV, and autonomous mobility.",
        role="Trainee Software Engineer (Embedded / C++)",
        ctc_total="₹ 4.50 LPA – ₹ 6.00 LPA",
        ctc_items=[{"label": "Fixed CTC", "value": "₹ 4.50 – ₹ 6.00 LPA"}],
        eligibility=["60% in 10th, 12th, and B.E / B.Tech (CSE/ECE/EEE/Mech)."],
        recruitment_process=["1. Aptitude + Embedded C / C++ Test", "2. Technical Interview", "3. HR Interview"],
        topics_covered=["Embedded C & Pointers", "Bitwise Operations", "Microcontrollers & RTOS", "Aptitude"],
        important_note=["Strong focus on C pointers, bitwise manipulation, and memory layout."],
        exam_style="KPIT style: C pointers, bitwise operators, volatile/static keywords, and embedded systems MCQs.",
        sample_questions=[
            {"title": "Sample 1: C `volatile` Keyword", "problem": "Why is `volatile` used in Embedded C?", "explanation": "It prevents the compiler from caching a variable in a register when hardware/ISRs can modify it asynchronously."},
            {"title": "Sample 2: Bitwise — Set Bit", "problem": "How do you set the `k`-th bit (0-indexed) of integer `n`?", "explanation": "`n |= (1 << k);`"},
            {"title": "Sample 3: Memory Segments", "problem": "Where are uninitialized global variables stored in C?", "explanation": "In the BSS segment."},
        ],
    ),
    _make_service_company(
        slug="adp",
        name="ADP",
        about="ADP is a global leader in cloud-based human capital management (HCM) and payroll software.",
        role="Member Technical (Software Engineer)",
        ctc_total="₹ 6.00 LPA – ₹ 7.00 LPA",
        ctc_items=[{"label": "Base + Bonus", "value": "₹ 6.00 – ₹ 7.00 LPA"}],
        eligibility=["65% or 6.5 CGPA in B.E / B.Tech (CSE/IT/ECE).", "No active backlogs."],
        recruitment_process=["1. Aptitude + Java/SQL/DSA Test", "2. Technical Interviews", "3. HR Round"],
        topics_covered=["Java & OOP", "SQL & DBMS", "Data Structures", "Quantitative Aptitude"],
        important_note=["Focus on enterprise Java, REST APIs, and relational database design."],
        exam_style="ADP style: Java OOP/Collections, SQL queries, REST/HTTP basics, and quantitative aptitude.",
        sample_questions=[
            {"title": "Sample 1: REST Status Codes", "problem": "Which HTTP status code represents 'Created' after a successful POST?", "explanation": "201 Created."},
            {"title": "Sample 2: SQL — Self Join", "problem": "How do you query an employee along with their manager's name from one `Employees` table?", "explanation": "Use a Self Join: `JOIN Employees m ON e.manager_id = m.id`."},
            {"title": "Sample 3: Quantitative — Percentage", "problem": "If salary increases by 20% and then decreases by 20%, what is net change?", "explanation": "-4% (0.8 * 1.2 = 0.96)."},
        ],
    ),
    _make_service_company(
        slug="ntt-data",
        name="NTT Data",
        about="NTT Data is a top-10 global IT services and consulting provider headquartered in Tokyo.",
        role="Software Development Senior Associate",
        ctc_total="₹ 4.00 LPA – ₹ 5.00 LPA",
        ctc_items=[{"label": "Fixed CTC", "value": "₹ 4.00 – ₹ 5.00 LPA"}],
        eligibility=["60% in 10th, 12th, Graduation.", "No active backlogs."],
        recruitment_process=["1. AMCAT Aptitude + Tech", "2. Technical Interview", "3. HR Interview"],
        topics_covered=["Quant & Reasoning", "Verbal English", "C/Java/SQL Basics"],
        important_note=["Conducted on AMCAT."],
        exam_style="NTT Data style: AMCAT quant, logical reasoning, verbal ability, and C/Java/SQL basics.",
        sample_questions=[
            {"title": "Sample 1: Time & Distance", "problem": "A cyclist covers 24 km in 2 hours. Speed in m/s?", "explanation": "12 km/hr * 5/18 = 3.33 m/s."},
            {"title": "Sample 2: DBMS — Normalization", "problem": "Which normal form eliminates partial dependencies on a composite key?", "explanation": "Second Normal Form (2NF)."},
            {"title": "Sample 3: C — `sizeof`", "problem": "What is `sizeof(char)` in C?", "explanation": "Guaranteed to be 1 byte by the C standard."},
        ],
    ),
]

COMPANY_BY_SLUG = {c["slug"]: c for c in COMPANIES}
COMPANY_TIERS = ["All", "Service Based", "Product & Tech", "Consulting & FinTech"]
