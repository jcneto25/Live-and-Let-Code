"""Testes de hashing canonico — base do replay deterministico (Fase 7)."""

from llc_trace.hashing import canonical_json, hash_file, input_hash, sha256_hex


def test_canonical_json_ignores_insertion_order():
    a = {"b": 1, "a": 2, "c": {"z": 1, "y": 2}}
    b = {"c": {"y": 2, "z": 1}, "a": 2, "b": 1}
    assert canonical_json(a) == canonical_json(b)


def test_canonical_json_is_compact():
    assert canonical_json({"a": 1, "b": 2}) == '{"a":1,"b":2}'


def test_canonical_json_handles_non_serializable():
    # default=str — nunca levanta (INV-T1)
    out = canonical_json({"path": __import__("pathlib").Path("x")})
    assert '"path":"x"' in out


def test_sha256_hex_accepts_str_and_bytes():
    assert sha256_hex("abc") == sha256_hex(b"abc")


def test_input_hash_has_algorithm_prefix():
    assert input_hash({"a": 1}).startswith("sha256:")


def test_input_hash_is_stable_across_key_order():
    assert input_hash({"a": 1, "b": 2}) == input_hash({"b": 2, "a": 1})


def test_input_hash_distinguishes_payloads():
    assert input_hash({"a": 1}) != input_hash({"a": 2})


def test_input_hash_of_str_is_direct():
    # string nao passa por JSON: hash do texto puro
    assert input_hash("abc") == f"sha256:{sha256_hex('abc')}"


def test_input_hash_scalars_and_collections():
    assert input_hash(None) != input_hash(0)
    assert input_hash([1, 2]) != input_hash([2, 1])


def test_hash_file_missing_returns_none():
    assert hash_file("/caminho/inexistente/arquivo.json") is None


def test_hash_file_content(tmp_path):
    p = tmp_path / "gates.json"
    p.write_text('{"gates":{}}', encoding="utf-8")
    h = hash_file(p)
    assert h is not None and h.startswith("sha256:")
    assert h == hash_file(p)
