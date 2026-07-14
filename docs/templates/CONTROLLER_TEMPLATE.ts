/**
 * Controller Template — LLC API Design Compliant
 *
 * Este template segue as diretrizes de API Design do LLC baseadas em
 * "Principles of Web API Design" (James Higginbotham) — processo ADD-R
 * e convenções REST.
 *
 * Checklist de conformidade (verificado por fitness-functions.py --check-api-design):
 *  [ ] @Controller path com prefixo de versão (ex: 'api/v1/auditorias')
 *  [ ] @HttpCode explícito em todos os endpoints
 *  [ ] @ApiResponse para 401, 403, 404, 422 em todos os endpoints
 *  [ ] PATCH para atualizações parciais; PUT apenas para substituição completa
 *  [ ] Nenhum endpoint RPC (POST /concluir, /suspender, etc.) — usar PATCH { status }
 *  [ ] Query params em camelCase (ex: ?page=1&limit=20&arquivoPath=...)
 *  [ ] Paths em kebab-case consistente (português para termos de domínio)
 *  [ ] Recursos aninhados modelados como paths aninhados (/auditorias/:id/achados)
 *  [ ] Paginação com envelope padrão { data, total, page, limit, totalPages }
 *  [ ] HATEOAS links (_links) em respostas de recurso único
 *  [ ] DTOs tipados (sem 'any') para request/response
 *  [ ] BearerAuth documentado no OpenAPI
 */

import {
  Controller,
  Get,
  Post,
  Put,
  Patch,
  Delete,
  Param,
  Query,
  Body,
  HttpCode,
  HttpStatus,
  ParseUUIDPipe,
} from '@nestjs/common';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiBearerAuth,
  ApiQuery,
  ApiParam,
} from '@nestjs/swagger';

// DTOs — substituir pelos DTOs reais do módulo
import { CreateRecursoDto } from './dto/create-recurso.dto';
import { UpdateRecursoDto } from './dto/update-recurso.dto';
import { RecursoReadModel } from '../domain/recurso.read-model';
import { PaginatedResponse } from '../../common/dto/paginated-response.dto';
import { RecursoService } from './recurso.service';

@ApiTags('Recursos')
@ApiBearerAuth('BearerAuth')
@Controller('api/v1/recursos')
export class RecursoController {
  constructor(private readonly recursoService: RecursoService) {}

  // ============================================
  // LIST — GET /api/v1/recursos
  // ============================================
  @Get()
  @HttpCode(HttpStatus.OK)
  @ApiOperation({
    summary: 'Listar recursos',
    description: 'Retorna lista paginada de recursos com filtros opcionais',
  })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Lista paginada de recursos',
    type: PaginatedResponse<RecursoReadModel>,
  })
  @ApiResponse({ status: HttpStatus.UNAUTHORIZED, description: 'Não autenticado' })
  @ApiResponse({ status: HttpStatus.FORBIDDEN, description: 'Acesso negado' })
  @ApiResponse({ status: HttpStatus.UNPROCESSABLE_ENTITY, description: 'Erro de validação' })
  @ApiQuery({ name: 'page', required: false, type: Number, example: 1, description: 'Número da página (1-indexed)' })
  @ApiQuery({ name: 'limit', required: false, type: Number, example: 20, description: 'Itens por página (máx: 100)' })
  @ApiQuery({ name: 'search', required: false, type: String, description: 'Termo de busca textual' })
  @ApiQuery({ name: 'status', required: false, type: String, description: 'Filtrar por status' })
  async findAll(
    @Query('page') page = 1,
    @Query('limit') limit = 20,
    @Query('search') search?: string,
    @Query('status') status?: string,
  ): Promise<PaginatedResponse<RecursoReadModel>> {
    const result = await this.recursoService.findAll({
      page: Math.max(1, page),
      limit: Math.min(100, Math.max(1, limit)),
      search,
      status,
    });

    return {
      data: result.data,
      total: result.total,
      page: result.page,
      limit: result.limit,
      totalPages: Math.ceil(result.total / result.limit),
      _links: {
        self: `/api/v1/recursos?page=${result.page}&limit=${result.limit}`,
        first: `/api/v1/recursos?page=1&limit=${result.limit}`,
        last: `/api/v1/recursos?page=${Math.ceil(result.total / result.limit)}&limit=${result.limit}`,
        next: result.page < Math.ceil(result.total / result.limit)
          ? `/api/v1/recursos?page=${result.page + 1}&limit=${result.limit}`
          : null,
        prev: result.page > 1
          ? `/api/v1/recursos?page=${result.page - 1}&limit=${result.limit}`
          : null,
      },
    };
  }

  // ============================================
  // GET ONE — GET /api/v1/recursos/:id
  // ============================================
  @Get(':id')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({
    summary: 'Obter recurso por ID',
    description: 'Retorna detalhes completos de um recurso específico',
  })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Recurso encontrado',
    type: RecursoReadModel,
  })
  @ApiResponse({ status: HttpStatus.UNAUTHORIZED, description: 'Não autenticado' })
  @ApiResponse({ status: HttpStatus.FORBIDDEN, description: 'Acesso negado' })
  @ApiResponse({ status: HttpStatus.NOT_FOUND, description: 'Recurso não encontrado' })
  @ApiResponse({ status: HttpStatus.UNPROCESSABLE_ENTITY, description: 'Erro de validação' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid', description: 'UUID do recurso' })
  async findOne(
    @Param('id', ParseUUIDPipe) id: string,
  ): Promise<RecursoReadModel & { _links: Record<string, string | null> }> {
    const recurso = await this.recursoService.findOne(id);

    return {
      ...recurso,
      _links: {
        self: `/api/v1/recursos/${id}`,
        collection: '/api/v1/recursos',
        // Adicionar links para recursos relacionados conforme aplicável
        // achados: `/api/v1/recursos/${id}/achados`,
        // evidencias: `/api/v1/recursos/${id}/evidencias`,
      },
    };
  }

  // ============================================
  // CREATE — POST /api/v1/recursos
  // ============================================
  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({
    summary: 'Criar novo recurso',
    description: 'Cria um novo recurso com os dados fornecidos',
  })
  @ApiResponse({
    status: HttpStatus.CREATED,
    description: 'Recurso criado com sucesso',
    type: RecursoReadModel,
  })
  @ApiResponse({ status: HttpStatus.UNAUTHORIZED, description: 'Não autenticado' })
  @ApiResponse({ status: HttpStatus.FORBIDDEN, description: 'Acesso negado' })
  @ApiResponse({ status: HttpStatus.UNPROCESSABLE_ENTITY, description: 'Erro de validação' })
  @ApiResponse({ status: HttpStatus.CONFLICT, description: 'Conflito (ex: duplicidade)' })
  async create(
    @Body() createDto: CreateRecursoDto,
  ): Promise<RecursoReadModel> {
    return this.recursoService.create(createDto);
  }

  // ============================================
  // FULL UPDATE — PUT /api/v1/recursos/:id
  // ============================================
  @Put(':id')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({
    summary: 'Substituir recurso completamente',
    description: 'Substitui todos os campos do recurso (idempotente). Use PATCH para atualização parcial.',
  })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Recurso substituído com sucesso',
    type: RecursoReadModel,
  })
  @ApiResponse({ status: HttpStatus.UNAUTHORIZED, description: 'Não autenticado' })
  @ApiResponse({ status: HttpStatus.FORBIDDEN, description: 'Acesso negado' })
  @ApiResponse({ status: HttpStatus.NOT_FOUND, description: 'Recurso não encontrado' })
  @ApiResponse({ status: HttpStatus.UNPROCESSABLE_ENTITY, description: 'Erro de validação' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid', description: 'UUID do recurso' })
  async replace(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() updateDto: UpdateRecursoDto, // DTO com todos os campos obrigatórios
  ): Promise<RecursoReadModel> {
    return this.recursoService.replace(id, updateDto);
  }

  // ============================================
  // PARTIAL UPDATE — PATCH /api/v1/recursos/:id
  // ============================================
  @Patch(':id')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({
    summary: 'Atualizar recurso parcialmente',
    description: 'Atualiza apenas os campos fornecidos. Para mudanças de status, use status no body.',
  })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Recurso atualizado com sucesso',
    type: RecursoReadModel,
  })
  @ApiResponse({ status: HttpStatus.UNAUTHORIZED, description: 'Não autenticado' })
  @ApiResponse({ status: HttpStatus.FORBIDDEN, description: 'Acesso negado' })
  @ApiResponse({ status: HttpStatus.NOT_FOUND, description: 'Recurso não encontrado' })
  @ApiResponse({ status: HttpStatus.UNPROCESSABLE_ENTITY, description: 'Erro de validação' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid', description: 'UUID do recurso' })
  async update(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() updateDto: UpdateRecursoDto, // DTO com campos opcionais (PartialType)
  ): Promise<RecursoReadModel> {
    return this.recursoService.update(id, updateDto);
  }

  // ============================================
  // STATUS TRANSITION — PATCH /api/v1/recursos/:id
  // (usar o mesmo endpoint PATCH com status no body)
  // NÃO usar: POST /recursos/:id/concluir, POST /recursos/:id/suspender, etc.
  // ============================================
  // Exemplo de body para transição de status:
  // { "status": "CONCLUIDO", "motivo": "Concluído conforme planejado" }

  // ============================================
  // DELETE — DELETE /api/v1/recursos/:id
  // ============================================
  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({
    summary: 'Excluir recurso',
    description: 'Remove permanentemente um recurso (soft delete recomendado)',
  })
  @ApiResponse({ status: HttpStatus.NO_CONTENT, description: 'Recurso excluído com sucesso' })
  @ApiResponse({ status: HttpStatus.UNAUTHORIZED, description: 'Não autenticado' })
  @ApiResponse({ status: HttpStatus.FORBIDDEN, description: 'Acesso negado' })
  @ApiResponse({ status: HttpStatus.NOT_FOUND, description: 'Recurso não encontrado' })
  @ApiParam({ name: 'id', type: 'string', format: 'uuid', description: 'UUID do recurso' })
  async remove(
    @Param('id', ParseUUIDPipe) id: string,
  ): Promise<void> {
    await this.recursoService.remove(id);
  }

  // ============================================
  // NESTED RESOURCES — Sub-recursos
  // Exemplo: GET /api/v1/recursos/:recursoId/achados
  // ============================================
  // Estes devem ser movidos para controllers separados (ex: AchadosController)
  // com @Controller('api/v1/recursos/:recursoId/achados')
  // e injetados via módulo pai.
}
