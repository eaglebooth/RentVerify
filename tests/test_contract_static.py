import ast
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "RentVerify.py"


class RentVerifyStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = CONTRACT.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_required_header(self):
        lines = self.source.splitlines()
        self.assertEqual(lines[0], "# v0.2.16")
        self.assertEqual(
            lines[1],
            '# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }',
        )
        self.assertEqual(lines[2], "from genlayer import *")

    def test_allowed_imports_only(self):
        imports = [node for node in self.tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        rendered = []
        for node in imports:
            if isinstance(node, ast.ImportFrom):
                rendered.append(f"from {node.module} import *")
            else:
                rendered.extend(alias.name for alias in node.names)
        self.assertEqual(rendered, ["from genlayer import *", "typing", "json"])

    def test_public_methods_use_allowed_signature_types(self):
        allowed = {"u256", "str", "typing.Any"}
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            has_public_decorator = any(
                isinstance(dec, ast.Attribute)
                and dec.attr in {"write", "view"}
                and isinstance(dec.value, ast.Attribute)
                and dec.value.attr == "public"
                for dec in node.decorator_list
            )
            if not has_public_decorator:
                continue
            for arg in node.args.args[1:]:
                annotation = ast.unparse(arg.annotation)
                self.assertIn(annotation, allowed, f"{node.name}.{arg.arg} has {annotation}")
            if node.returns is not None:
                self.assertIn(ast.unparse(node.returns), allowed)

    def test_nondeterminism_wrapped_in_strict_eq(self):
        self.assertIn("gl.eq_principle.strict_eq(run_review)", self.source)
        self.assertIn("gl.nondet.web.render", self.source)
        self.assertIn("gl.nondet.exec_prompt", self.source)

    def test_has_explicit_edge_case_codes(self):
        for code in [
            "INVALID_CASE_ID",
            "INVALID_DEPOSIT",
            "WEB_RENDER_FAILED",
            "INVALID_AI_RESPONSE",
            "AI_DECISION_INCONSISTENT",
            "PAYOUT_MISMATCH",
        ]:
            self.assertIn(code, self.source)


if __name__ == "__main__":
    unittest.main()
