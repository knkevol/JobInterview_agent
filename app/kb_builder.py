# LLM이 만든 knowledge base에 tree-sitter로 계산한 정확한 근거를 붙여주는 역할을 담당하는 모듈
# code_reader는 무엇이 있는지, kb_builder는 정확히 몇번째줄인지 등의 정확한 근거를 파이썬이 직접 계산

from tree_sitter import Language, Parser
import tree_sitter_cpp as tscpp

CPP_LANGUAGE = Language(tscpp.language())

# 이름 정규화 : 첫 번째 "(" 이후는 전부 잘라낸다.
def _normalize_name(name: str | None) -> str | None:
    if name is None:
        return None
    paren_index = name.find("(")
    if paren_index != -1:
        name = name[:paren_index]
    return name.strip()

# 클래스 이름 추출
def _get_class_name(node, source_bytes: bytes) -> str | None:
    name_node = node.child_by_field_name("name")
    if name_node is None:
        return None
    return source_bytes[name_node.start_byte:name_node.end_byte].decode("utf8", errors="replace")

# 함수 이름 추출
def _get_function_name(node, source_bytes: bytes) -> str | None:
    declarator = node.child_by_field_name("declarator")

    while declarator is not None:
        if declarator.type in ("identifier", "field_identifier"):
                # 함수 이름만 있는 경우
                return source_bytes[declarator.start_byte:declarator.end_byte].decode("utf8", errors="replace")
        if declarator.type == "qualified_identifier":
            # classname::methodname 형태 : "::" 뒤 진짜 이름만 사용
            name_node = declarator.child_by_field_name("name")
            if name_node is not None:
                 return source_bytes[name_node.start_byte:name_node.end_byte].decode("utf8", errors="replace")
            return None

        declarator = declarator.child_by_field_name("declarator")
        
    return None


def extract_evidence(source_code: str) -> dict:
    parser = Parser(CPP_LANGUAGE)
    source_bytes = source_code.encode("utf8")
    tree = parser.parse(source_bytes)

    source_lines = source_code.splitlines()

    evidence: dict[str, dict] = {}

    def make_evidence(node) -> dict:
        # node.start_point / end_point는 (row, column) 튜플이고, row는 0부터 센다.
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        snippet_lines = source_lines[start_line - 1:end_line]
        return {
            "start_line": start_line,
            "end_line": end_line,
            "snippet": "\n".join(snippet_lines)
        }

    def visit(node) -> None:
        if node.type in ["class_specifier", "struct_specifier"]:
            class_name = _get_class_name(node, source_bytes)
            if class_name:
                evidence[class_name] = make_evidence(node)
                evidence[_normalize_name(class_name)] = make_evidence(node)

        elif node.type == "function_definition":
            function_name = _get_function_name(node, source_bytes)
            if function_name:
                evidence[function_name] = make_evidence(node)
                evidence[_normalize_name(function_name)] = make_evidence(node)

        for child in node.children:
            visit(child)

    visit(tree.root_node)
    return evidence

def attach_evidence(kb_entry: dict, source_code: str) -> dict:
    evidence_map = extract_evidence(source_code)

    for class_info in kb_entry.get("classes", []):
        class_name = class_info.get("name")
        class_info["evidence"] = evidence_map.get(class_name)
        class_info["evidence"] = evidence_map.get(_normalize_name(class_name))

        for method_info in class_info.get("methods", []):
            method_name = method_info.get("name")
            method_info["evidence"] = evidence_map.get(method_name)
            method_info["evidence"] = evidence_map.get(_normalize_name(method_name))

    return kb_entry
