#!/usr/bin/env python3
"""Tests unitários para llc_wave.py."""

import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Adiciona o diretório de scripts ao path
sys.path.insert(0, str(Path(__file__).parent))

from llc_wave import (
    PrpInfo,
    WaveInfo,
    _find_prp_headings,
    _find_tasks_in_section,
    _find_wave_headings,
    _strip_placeholders,
    format_wave_list,
    parse_execution_waves,
    parse_tasks,
)


class TestWaveInfo:
    """Testes para a classe WaveInfo."""

    def test_init_with_all_params(self):
        """WaveInfo deve ser criado com todos os parâmetros."""
        wave = WaveInfo(number=1, name="Wave 1", prps=["PRP-001", "PRP-002"])
        assert wave.number == 1
        assert wave.name == "Wave 1"
        assert wave.prps == ["PRP-001", "PRP-002"]

    def test_init_with_empty_prps(self):
        """WaveInfo deve aceitar lista vazia de PRPs."""
        wave = WaveInfo(number=2, name="Wave 2", prps=[])
        assert wave.number == 2
        assert wave.prps == []

    def test_repr(self):
        """WaveInfo.__repr__ deve retornar string formatada."""
        wave = WaveInfo(number=1, name="Test Wave", prps=["PRP-001"])
        assert repr(wave) == "Wave 1: Test Wave (1 PRPs)"


class TestPrpInfo:
    """Testes para a classe PrpInfo."""

    def test_init_with_all_params(self):
        """PrpInfo deve ser criado com todos os parâmetros."""
        prp = PrpInfo(prp_id="PRP-001", name="Nome do PRP", tasks=["T-001", "T-002"])
        assert prp.prp_id == "PRP-001"
        assert prp.name == "Nome do PRP"
        assert prp.tasks == ["T-001", "T-002"]

    def test_init_without_tasks(self):
        """PrpInfo deve inicializar com lista vazia quando tasks=None."""
        prp = PrpInfo(prp_id="PRP-001")
        assert prp.prp_id == "PRP-001"
        assert prp.tasks == []

    def test_init_with_empty_tasks(self):
        """PrpInfo deve aceitar lista vazia de tasks."""
        prp = PrpInfo(prp_id="PRP-001", tasks=[])
        assert prp.tasks == []

    def test_init_with_tasks(self):
        """PrpInfo deve copiar a lista de tasks."""
        tasks = ["T-001", "T-002"]
        prp = PrpInfo(prp_id="PRP-001", tasks=tasks)
        assert prp.tasks == ["T-001", "T-002"]
        # Modificar a lista original não deve afetar prp.tasks
        tasks.append("T-003")
        assert prp.tasks == ["T-001", "T-002"]

    def test_repr(self):
        """PrpInfo.__repr__ deve retornar string formatada."""
        prp = PrpInfo(prp_id="PRP-001", name="Nome", tasks=["T-001"])
        assert repr(prp) == "PRP-001: Nome (1 tasks)"


class TestStripPlaceholders:
    """Testes para _strip_placeholders."""

    def test_removes_placeholder(self):
        """Deve remover placeholders no formato {N}."""
        result = _strip_placeholders("Texto com {N} placeholder")
        assert result == "Texto com  placeholder"

    def test_removes_multiple_placeholders(self):
        """Deve remover múltiplos placeholders."""
        result = _strip_placeholders("{Nome} {Data} {N}")
        assert result == "   "

    def test_preserves_text(self):
        """Deve preservar texto fora dos placeholders."""
        result = _strip_placeholders("Texto sem placeholders")
        assert result == "Texto sem placeholders"


class TestFindWaveHeadings:
    """Testes para _find_wave_headings."""

    def test_finds_single_wave(self):
        """Deve encontrar uma única onda."""
        content = "### Onda 1: Nome da Onda"
        result = _find_wave_headings(content)
        assert len(result) == 1
        assert result[0][0] == 0  # start_line
        assert result[0][1] == 0  # heading_line
        assert result[0][2] == "Nome da Onda"  # name
        assert result[0][3] == 1  # wave_number

    def test_finds_multiple_waves(self):
        """Deve encontrar múltiplas ondas."""
        content = "### Onda 1: Primeira\n### Onda 2: Segunda\n### Onda 3: Terceira"
        result = _find_wave_headings(content)
        assert len(result) == 3
        assert result[0][3] == 1
        assert result[1][3] == 2
        assert result[2][3] == 3

    def test_ignores_placeholders(self):
        """Deve ignorar headings com placeholders."""
        content = "### Onda {N}: {Nome}"
        result = _find_wave_headings(content)
        assert len(result) == 0

    def test_handles_extra_whitespace(self):
        """Deve lidar com espaços extras."""
        content = "###   Onda   5   :   Nome da Onda   "
        result = _find_wave_headings(content)
        assert len(result) == 1
        assert result[0][3] == 5
        assert result[0][2] == "Nome da Onda"


class TestFindPrpHeadings:
    """Testes para _find_prp_headings."""

    def test_finds_single_prp(self):
        """Deve encontrar um único PRP."""
        content = "#### PRP-001: ID — Nome do PRP"
        result = _find_prp_headings(content)
        assert len(result) == 1
        assert result[0][1] == "PRP-001"
        assert "Nome do PRP" in result[0][2]

    def test_finds_prp_without_name(self):
        """Deve encontrar PRP sem nome após o traço."""
        content = "#### PRP-001: ID"
        result = _find_prp_headings(content)
        assert len(result) == 1
        assert result[0][1] == "PRP-001"


class TestFindTasksInSection:
    """Testes para _find_tasks_in_section."""

    def test_finds_task_in_checkbox(self):
        """Deve encontrar tarefa em checkbox."""
        section = "- [ ] Tarefa (T-001)"
        result = _find_tasks_in_section(section)
        assert result == ["T-001"]

    def test_finds_task_in_checkbox_checked(self):
        """Deve encontrar tarefa em checkbox marcado."""
        section = "- [x] Tarefa (T-001)"
        result = _find_tasks_in_section(section)
        assert result == ["T-001"]

    def test_finds_task_in_table(self):
        """Deve encontrar tarefa em tabela."""
        section = "| T-001 | Descrição |"
        result = _find_tasks_in_section(section)
        assert result == ["T-001"]

    def test_finds_multiple_tasks(self):
        """Deve encontrar múltiplas tarefas."""
        section = "- [ ] Tarefa 1 (T-001)\n- [ ] Tarefa 2 (T-002)\n| T-003 | Tarefa 3 |"
        result = _find_tasks_in_section(section)
        assert sorted(result) == ["T-001", "T-002", "T-003"]

    def test_ignores_tasks_outside_context(self):
        """Deve ignorar IDs de tarefas fora de contexto."""
        section = "Ver T-001 para mais detalhes"
        result = _find_tasks_in_section(section)
        assert result == []

    def test_handles_foundation_tasks(self):
        """Deve encontrar tasks FDN-*."""
        section = "| FDN-001 | Tarefa de Fundação |"
        result = _find_tasks_in_section(section)
        assert result == ["FDN-001"]


class TestParseExecutionWaves:
    """Testes para parse_execution_waves."""

    @patch("llc_wave.Path")
    def test_returns_empty_when_file_not_found(self, mock_path):
        """Deve retornar lista vazia se arquivo não existir."""
        mock_path.return_value.exists.return_value = False
        result = parse_execution_waves()
        assert result == []

    @patch("llc_wave.Path")
    def test_returns_empty_without_waves(self, mock_path):
        """Deve retornar lista vazia sem headings de ondas."""
        mock_path.return_value.exists.return_value = True
        mock_path.return_value.read_text.return_value = "Texto sem ondas"
        result = parse_execution_waves()
        assert result == []

    @patch("llc_wave.Path")
    def test_parses_waves_with_prps(self, mock_path):
        """Deve parsear ondas com PRPs associados."""
        mock_path.return_value.exists.return_value = True
        content = """
### Onda 1: Primeira Onda

| PRP-001 | Descrição |
| PRP-002 | Descrição |
"""
        mock_path.return_value.read_text.return_value = content
        result = parse_execution_waves()
        assert len(result) == 1
        assert result[0].number == 1
        assert "PRP-001" in result[0].prps
        assert "PRP-002" in result[0].prps


class TestParseTasks:
    """Testes para parse_tasks."""

    @patch("llc_wave.Path")
    def test_returns_empty_when_file_not_found(self, mock_path):
        """Deve retornar dicionário vazio se arquivo não existir."""
        mock_path.return_value.exists.return_value = False
        result = parse_tasks()
        assert result == {}

    @patch("llc_wave.Path")
    def test_returns_prps_from_headings(self, mock_path):
        """Deve extrair PRPs dos headings."""
        mock_path.return_value.exists.return_value = True
        content = """#### PRP-001: ID1 — Nome do PRP 1
- [ ] Tarefa (T-001)

#### PRP-002: ID2
- [x] Tarefa (T-002)
"""
        mock_path.return_value.read_text.return_value = content
        result = parse_tasks()
        assert "PRP-001" in result
        assert "PRP-002" in result
        assert result["PRP-001"].tasks == ["T-001"]
        assert result["PRP-002"].tasks == ["T-002"]


class TestFormatWaveList:
    """Testes para format_wave_list."""

    def test_formats_empty_list(self):
        """Deve retornar mensagem para lista vazia."""
        result = format_wave_list([], {})
        assert "Nenhuma wave encontrada" in result

    def test_formats_single_wave(self):
        """Deve formatar uma única onda."""
        waves = [WaveInfo(number=1, name="Wave 1", prps=["PRP-001"])]
        prps = {"PRP-001": PrpInfo(prp_id="PRP-001", tasks=["T-001"])}
        result = format_wave_list(waves, prps)
        assert "Onda 1: Wave 1" in result
        assert "PRPs: 1" in result
        assert "Tasks: 1" in result

    def test_shows_tasks_for_prp(self):
        """Deve mostrar tasks associadas a cada PRP."""
        waves = [WaveInfo(number=1, name="Wave 1", prps=["PRP-001"])]
        prps = {"PRP-001": PrpInfo(prp_id="PRP-001", tasks=["T-001", "T-002"])}
        result = format_wave_list(waves, prps)
        assert "T-001" in result
        assert "T-002" in result


class TestPreWaveCheck:
    """_pre_wave_check deve existir, ser chamavel e retornar bool."""

    def test_pre_wave_check_is_defined_and_callable(self):
        from llc_wave import _pre_wave_check

        assert callable(_pre_wave_check)

    def test_pre_wave_check_true_when_script_missing(self, monkeypatch, tmp_path):
        import llc_wave

        monkeypatch.setattr(llc_wave, "PRE_WAVE_CHECK_SCRIPT", tmp_path / "absent.sh")
        assert llc_wave._pre_wave_check(dry_run=False, wave_num=1) is True


class TestPostWaveCheck:
    """_post_wave_check deve retornar bool (nao None)."""

    def test_post_wave_check_returns_true_when_script_missing(self, monkeypatch, tmp_path):
        import llc_wave

        monkeypatch.setattr(llc_wave, "PRE_WAVE_CHECK_SCRIPT", tmp_path / "absent.sh")
        monkeypatch.delenv("LLC_PRP_NO_VERIFY", raising=False)
        result = llc_wave._post_wave_check(dry_run=False, wave_num=1, prp_ids=None)
        assert result is True  # before fix the outer fn returns None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
