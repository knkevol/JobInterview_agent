# CS 지식 퀴즈 문제 은행

QUIZ_SEED_DATA = [
    {
        "category": "자료구조",
        "question": "가장 나중에 들어온 데이터가 가장 먼저 나가는(LIFO) 자료구조의 이름은?",
        "answer": "스택",
        "explanation": "스택(Stack)은 Last In First Out 구조로, push로 넣고 pop으로 꺼내며 함수 호출 스택, 실행 취소(undo) 등에 쓰인다.",
        "difficulty": 1,
    },
    {
        "category": "자료구조",
        "question": "가장 먼저 들어온 데이터가 가장 먼저 나가는(FIFO) 자료구조의 이름은?",
        "answer": "큐",
        "explanation": "큐(Queue)는 First In First Out 구조로, 대기열이나 작업 스케줄링, BFS 탐색 등에 쓰인다.",
        "difficulty": 1,
    },
    {
        "category": "알고리즘",
        "question": "정렬된 배열에서 이진 탐색(Binary Search)의 시간복잡도를 Big-O 표기법으로 쓰면?",
        "answer": "O(log n)",
        "explanation": "매 단계마다 탐색 범위를 절반으로 줄이기 때문에, 전체 원소 수가 n이어도 탐색 횟수는 log(n)에 비례한다.",
        "difficulty": 1,
    },
    {
        "category": "운영체제",
        "question": "프로세스 안에서 메모리(주소 공간)를 공유하며 동시에 실행되는 단위를 무엇이라 하나요?",
        "answer": "스레드",
        "explanation": "프로세스는 독립된 메모리 공간을 갖지만, 한 프로세스 안의 여러 스레드는 같은 메모리(코드/데이터/힙)를 공유하고 스택만 따로 갖는다.",
        "difficulty": 1,
    },
    {
        "category": "운영체제",
        "question": "실제 물리 메모리보다 큰 메모리 공간을 프로세스가 쓸 수 있게 해주는, 디스크를 메모리처럼 활용하는 기법은?",
        "answer": "가상 메모리",
        "explanation": "가상 메모리(Virtual Memory)는 프로세스마다 독립된 가상 주소 공간을 주고, 실제로는 페이지 단위로 물리 메모리/디스크(스왑)를 오가며 관리한다.",
        "difficulty": 2,
    },
    {
        "category": "네트워크",
        "question": "3-way handshake로 연결을 맺고 신뢰성 있는 전송을 보장하는 전송 계층 프로토콜은?",
        "answer": "TCP",
        "explanation": "TCP(Transmission Control Protocol)는 연결 지향적이며 순서 보장, 재전송, 흐름 제어를 제공한다. 반대로 UDP는 연결 없이 빠르게 보내지만 신뢰성을 보장하지 않는다.",
        "difficulty": 1,
    },
    {
        "category": "데이터베이스",
        "question": "테이블에서 특정 컬럼 검색 속도를 높이기 위해 별도로 만들어두는 자료구조는?",
        "answer": "인덱스",
        "explanation": "인덱스(Index)는 보통 B-Tree 구조로 만들어져 WHERE 조건 검색을 빠르게 해주지만, 데이터를 추가/수정할 때마다 함께 갱신해야 해서 쓰기 성능은 느려질 수 있다.",
        "difficulty": 2,
    },
    {
        "category": "C++",
        "question": "직접적인 소유자가 단 하나만 존재하도록 보장하고, 복사는 금지되며 이동(move)만 가능한 스마트 포인터는?",
        "answer": "unique_ptr",
        "explanation": "std::unique_ptr는 소유권이 단 하나의 포인터에만 있다는 걸 컴파일 타임에 강제한다. 여러 곳에서 소유권을 공유하려면 참조 카운트를 쓰는 shared_ptr를 대신 사용한다.",
        "difficulty": 2,
    },
]
