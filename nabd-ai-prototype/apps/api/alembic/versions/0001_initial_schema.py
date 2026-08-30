"""Initial schema for the isolated synthetic prototype.

Revision ID: 0001_initial_schema
Revises: none
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('audit_events',
    sa.Column('event_id', sa.String(length=96), nullable=False),
    sa.Column('chain_key', sa.String(length=64), nullable=False),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column('event_type', sa.String(length=48), nullable=False),
    sa.Column('case_id', sa.String(length=64), nullable=True),
    sa.Column('application_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('actor_id', sa.String(length=128), nullable=False),
    sa.Column('actor_kind', sa.String(length=32), nullable=False),
    sa.Column('outcome', sa.String(length=16), nullable=False),
    sa.Column('reason_code', sa.String(length=64), nullable=True),
    sa.Column('severity', sa.String(length=16), nullable=True),
    sa.Column('from_state', sa.String(length=48), nullable=True),
    sa.Column('to_state', sa.String(length=48), nullable=True),
    sa.Column('previous_event_hash', sa.String(length=64), nullable=False),
    sa.Column('event_hash', sa.String(length=64), nullable=False),
    sa.Column('confirmed', sa.Boolean(), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('event_id', name=op.f('pk_audit_events')),
    sa.UniqueConstraint('chain_key', 'sequence', name='uq_audit_events_chain_key')
    )
    op.create_index('ix_audit_events_case', 'audit_events', ['case_id'], unique=False)
    op.create_index('ix_audit_events_type', 'audit_events', ['event_type'], unique=False)
    op.create_table('authorization_decisions',
    sa.Column('authorization_id', sa.String(length=128), nullable=False),
    sa.Column('environment_id', sa.String(length=64), nullable=False),
    sa.Column('use_case_contract_id', sa.String(length=128), nullable=False),
    sa.Column('source_manifest_sha256', sa.String(length=64), nullable=False),
    sa.Column('demo_period_start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('demo_period_end', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked', sa.Boolean(), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('authorization_id', name=op.f('pk_authorization_decisions'))
    )
    op.create_table('cases',
    sa.Column('case_id', sa.String(length=64), nullable=False),
    sa.Column('requester_identity_id', sa.String(length=128), nullable=False),
    sa.Column('business_scope_id', sa.String(length=64), nullable=False),
    sa.Column('use_case_contract_id', sa.String(length=128), nullable=False),
    sa.Column('authorization_id', sa.String(length=128), nullable=False),
    sa.Column('raw_question', sa.Text(), nullable=False),
    sa.Column('normalised_question', sa.Text(), nullable=False),
    sa.Column('question_sha256', sa.String(length=64), nullable=False),
    sa.Column('current_state', sa.String(length=48), nullable=False),
    sa.Column('route', sa.String(length=32), nullable=True),
    sa.Column('reason_code', sa.String(length=64), nullable=True),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('stop_record', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('case_id', name=op.f('pk_cases'))
    )
    op.create_index('ix_cases_requester', 'cases', ['requester_identity_id'], unique=False)
    op.create_index('ix_cases_state', 'cases', ['current_state'], unique=False)
    op.create_table('defects',
    sa.Column('defect_id', sa.String(length=64), nullable=False),
    sa.Column('severity', sa.String(length=16), nullable=False),
    sa.Column('status', sa.String(length=24), nullable=False),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('reported_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('defect_id', name=op.f('pk_defects'))
    )
    op.create_table('demo_identities',
    sa.Column('identity_id', sa.String(length=128), nullable=False),
    sa.Column('role', sa.String(length=32), nullable=False),
    sa.Column('role_id', sa.String(length=64), nullable=False),
    sa.Column('business_scope_id', sa.String(length=64), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('selectable_in_ui', sa.Boolean(), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('identity_id', name=op.f('pk_demo_identities'))
    )
    op.create_table('evidence_records',
    sa.Column('evidence_record_id', sa.String(length=96), nullable=False),
    sa.Column('component_id', sa.String(length=96), nullable=False),
    sa.Column('component_version', sa.String(length=64), nullable=False),
    sa.Column('status_dimension', sa.String(length=32), nullable=False),
    sa.Column('evidence_type', sa.String(length=64), nullable=False),
    sa.Column('artifact_path', sa.Text(), nullable=False),
    sa.Column('artifact_sha256', sa.String(length=64), nullable=False),
    sa.Column('decision', sa.String(length=32), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('evidence_record_id', name=op.f('pk_evidence_records'))
    )
    op.create_table('kill_switch_events',
    sa.Column('kill_switch_event_id', sa.String(length=96), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('actor_id', sa.String(length=128), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('kill_switch_event_id', name=op.f('pk_kill_switch_events'))
    )
    op.create_table('model_configurations',
    sa.Column('model_configuration_id', sa.String(length=128), nullable=False),
    sa.Column('task_role', sa.String(length=16), nullable=False),
    sa.Column('model_revision', sa.String(length=128), nullable=False),
    sa.Column('prompt_version', sa.String(length=64), nullable=False),
    sa.Column('mode', sa.String(length=16), nullable=False),
    sa.Column('revoked', sa.Boolean(), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('model_configuration_id', name=op.f('pk_model_configurations'))
    )
    op.create_table('source_records',
    sa.Column('source_id', sa.String(length=64), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('owner', sa.Text(), nullable=False),
    sa.Column('authority_class', sa.String(length=48), nullable=False),
    sa.Column('business_scope_id', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('source_id', name=op.f('pk_source_records'))
    )
    op.create_table('status_records',
    sa.Column('status_record_id', sa.String(length=96), nullable=False),
    sa.Column('component_id', sa.String(length=96), nullable=False),
    sa.Column('component_version', sa.String(length=64), nullable=False),
    sa.Column('built', sa.String(length=24), nullable=False),
    sa.Column('integration', sa.String(length=24), nullable=False),
    sa.Column('operational', sa.String(length=24), nullable=False),
    sa.Column('authorization', sa.String(length=24), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('status_record_id', name=op.f('pk_status_records'))
    )
    op.create_table('tevv_runs',
    sa.Column('tevv_run_id', sa.String(length=96), nullable=False),
    sa.Column('plan_version', sa.String(length=48), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('executor', sa.String(length=128), nullable=False),
    sa.Column('component_versions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('summary', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('artifact_path', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('tevv_run_id', name=op.f('pk_tevv_runs'))
    )
    op.create_table('use_case_contracts',
    sa.Column('use_case_contract_id', sa.String(length=128), nullable=False),
    sa.Column('business_scope_id', sa.String(length=64), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('use_case_contract_id', name=op.f('pk_use_case_contracts'))
    )
    op.create_table('case_state_transitions',
    sa.Column('transition_id', sa.String(length=96), nullable=False),
    sa.Column('case_id', sa.String(length=64), nullable=False),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column('from_state', sa.String(length=48), nullable=True),
    sa.Column('to_state', sa.String(length=48), nullable=False),
    sa.Column('reason_code', sa.String(length=64), nullable=True),
    sa.Column('actor_id', sa.String(length=128), nullable=False),
    sa.Column('actor_kind', sa.String(length=32), nullable=False),
    sa.Column('component_versions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('applicable_rule_versions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_case_state_transitions_case_id_cases')),
    sa.PrimaryKeyConstraint('transition_id', name=op.f('pk_case_state_transitions')),
    sa.UniqueConstraint('case_id', 'sequence', name='uq_case_state_transitions_case_id')
    )
    op.create_index('ix_case_state_transitions_case', 'case_state_transitions', ['case_id'], unique=False)
    op.create_table('decision_packets',
    sa.Column('packet_id', sa.String(length=96), nullable=False),
    sa.Column('case_id', sa.String(length=64), nullable=False),
    sa.Column('packet_version', sa.Integer(), nullable=False),
    sa.Column('route', sa.String(length=32), nullable=False),
    sa.Column('packet_sha256', sa.String(length=64), nullable=False),
    sa.Column('canonical_json', sa.Text(), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('pre_issuance_event_id', sa.String(length=96), nullable=True),
    sa.Column('displayable', sa.Boolean(), nullable=False),
    sa.Column('superseded_by_version', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_decision_packets_case_id_cases')),
    sa.PrimaryKeyConstraint('packet_id', name=op.f('pk_decision_packets')),
    sa.UniqueConstraint('case_id', 'packet_version', name='uq_decision_packets_case_id')
    )
    op.create_index('ix_decision_packets_case', 'decision_packets', ['case_id'], unique=False)
    op.create_table('demo_sessions',
    sa.Column('session_id', sa.String(length=128), nullable=False),
    sa.Column('identity_id', sa.String(length=128), nullable=False),
    sa.Column('issued_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked', sa.Boolean(), nullable=False),
    sa.Column('token_sha256', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['identity_id'], ['demo_identities.identity_id'], name=op.f('fk_demo_sessions_identity_id_demo_identities')),
    sa.PrimaryKeyConstraint('session_id', name=op.f('pk_demo_sessions')),
    sa.UniqueConstraint('token_sha256', name=op.f('uq_demo_sessions_token_sha256'))
    )
    op.create_index(op.f('ix_demo_sessions_identity_id'), 'demo_sessions', ['identity_id'], unique=False)
    op.create_table('deterministic_results',
    sa.Column('deterministic_result_id', sa.String(length=96), nullable=False),
    sa.Column('case_id', sa.String(length=64), nullable=False),
    sa.Column('rule_id', sa.String(length=32), nullable=False),
    sa.Column('rule_version', sa.String(length=32), nullable=False),
    sa.Column('outcome', sa.String(length=16), nullable=False),
    sa.Column('reason_code', sa.String(length=64), nullable=False),
    sa.Column('effect', sa.String(length=32), nullable=False),
    sa.Column('precedence_rank', sa.Integer(), nullable=False),
    sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_deterministic_results_case_id_cases')),
    sa.PrimaryKeyConstraint('deterministic_result_id', name=op.f('pk_deterministic_results'))
    )
    op.create_index('ix_deterministic_results_case', 'deterministic_results', ['case_id'], unique=False)
    op.create_table('evidence_excerpts',
    sa.Column('excerpt_id', sa.String(length=96), nullable=False),
    sa.Column('case_id', sa.String(length=64), nullable=False),
    sa.Column('source_id', sa.String(length=64), nullable=False),
    sa.Column('source_version', sa.String(length=32), nullable=False),
    sa.Column('source_version_key', sa.String(length=128), nullable=False),
    sa.Column('page_number', sa.Integer(), nullable=False),
    sa.Column('section_heading', sa.Text(), nullable=False),
    sa.Column('block_index', sa.Integer(), nullable=False),
    sa.Column('char_start', sa.Integer(), nullable=False),
    sa.Column('char_end', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('text_sha256', sa.String(length=64), nullable=False),
    sa.Column('source_sha256', sa.String(length=64), nullable=False),
    sa.Column('rank', sa.Integer(), nullable=False),
    sa.Column('retrieval_score', sa.Integer(), nullable=False),
    sa.Column('admitted', sa.Boolean(), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_evidence_excerpts_case_id_cases')),
    sa.PrimaryKeyConstraint('excerpt_id', name=op.f('pk_evidence_excerpts')),
    sa.UniqueConstraint('case_id', 'excerpt_id', name='uq_evidence_excerpts_case_id')
    )
    op.create_index('ix_evidence_excerpts_case', 'evidence_excerpts', ['case_id'], unique=False)
    op.create_table('generated_claims',
    sa.Column('claim_id', sa.String(length=96), nullable=False),
    sa.Column('case_id', sa.String(length=64), nullable=False),
    sa.Column('claim_ref', sa.String(length=8), nullable=False),
    sa.Column('statement', sa.Text(), nullable=False),
    sa.Column('materiality', sa.String(length=16), nullable=False),
    sa.Column('support_state', sa.String(length=24), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_generated_claims_case_id_cases')),
    sa.PrimaryKeyConstraint('claim_id', name=op.f('pk_generated_claims')),
    sa.UniqueConstraint('case_id', 'claim_ref', name='uq_generated_claims_case_id')
    )
    op.create_index(op.f('ix_generated_claims_case_id'), 'generated_claims', ['case_id'], unique=False)
    op.create_table('human_dispositions',
    sa.Column('disposition_id', sa.String(length=96), nullable=False),
    sa.Column('case_id', sa.String(length=64), nullable=False),
    sa.Column('packet_id', sa.String(length=96), nullable=False),
    sa.Column('packet_version', sa.Integer(), nullable=False),
    sa.Column('packet_sha256', sa.String(length=64), nullable=False),
    sa.Column('reviewer_identity_id', sa.String(length=128), nullable=False),
    sa.Column('disposition_value', sa.String(length=32), nullable=False),
    sa.Column('human_rationale', sa.Text(), nullable=False),
    sa.Column('is_final', sa.Boolean(), nullable=False),
    sa.Column('decided_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('closure_event_id', sa.String(length=96), nullable=True),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_human_dispositions_case_id_cases')),
    sa.PrimaryKeyConstraint('disposition_id', name=op.f('pk_human_dispositions'))
    )
    op.create_index(op.f('ix_human_dispositions_case_id'), 'human_dispositions', ['case_id'], unique=False)
    op.create_index('uq_human_dispositions_final_per_packet', 'human_dispositions', ['packet_id', 'packet_version'], unique=True, postgresql_where=sa.text('is_final'), sqlite_where=sa.text('is_final = 1'))
    op.create_table('model_runs',
    sa.Column('model_run_id', sa.String(length=96), nullable=False),
    sa.Column('case_id', sa.String(length=64), nullable=False),
    sa.Column('model_configuration_id', sa.String(length=128), nullable=False),
    sa.Column('task_role', sa.String(length=16), nullable=False),
    sa.Column('call_index', sa.Integer(), nullable=False),
    sa.Column('retry_count', sa.Integer(), nullable=False),
    sa.Column('input_chars', sa.Integer(), nullable=False),
    sa.Column('output_chars', sa.Integer(), nullable=False),
    sa.Column('input_sha256', sa.String(length=64), nullable=False),
    sa.Column('output_sha256', sa.String(length=64), nullable=False),
    sa.Column('duration_ms', sa.Integer(), nullable=False),
    sa.Column('succeeded', sa.Boolean(), nullable=False),
    sa.Column('reason_code', sa.String(length=64), nullable=True),
    sa.Column('mode', sa.String(length=16), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('call_index >= 1 AND call_index <= 2', name=op.f('ck_model_runs_call_index_within_budget')),
    sa.CheckConstraint('retry_count >= 0 AND retry_count <= 1', name=op.f('ck_model_runs_retry_within_budget')),
    sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_model_runs_case_id_cases')),
    sa.PrimaryKeyConstraint('model_run_id', name=op.f('pk_model_runs')),
    sa.UniqueConstraint('case_id', 'task_role', 'call_index', name='uq_model_runs_case_id')
    )
    op.create_index(op.f('ix_model_runs_case_id'), 'model_runs', ['case_id'], unique=False)
    op.create_table('source_versions',
    sa.Column('source_version_key', sa.String(length=128), nullable=False),
    sa.Column('source_id', sa.String(length=64), nullable=False),
    sa.Column('source_version', sa.String(length=32), nullable=False),
    sa.Column('lifecycle', sa.String(length=16), nullable=False),
    sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
    sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('superseded_by', sa.String(length=128), nullable=True),
    sa.Column('quarantine_reason', sa.Text(), nullable=True),
    sa.Column('business_scope_id', sa.String(length=64), nullable=False),
    sa.Column('access_labels', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('permitted_use_case_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('source_path', sa.Text(), nullable=False),
    sa.Column('source_sha256', sa.String(length=64), nullable=False),
    sa.Column('extracted_text_sha256', sa.String(length=64), nullable=False),
    sa.Column('instruction_like_flags', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['source_id'], ['source_records.source_id'], name=op.f('fk_source_versions_source_id_source_records')),
    sa.PrimaryKeyConstraint('source_version_key', name=op.f('pk_source_versions')),
    sa.UniqueConstraint('source_id', 'source_version', name='uq_source_versions_source_id')
    )
    op.create_index('ix_source_versions_lifecycle', 'source_versions', ['lifecycle'], unique=False)
    op.create_table('tevv_results',
    sa.Column('tevv_result_id', sa.String(length=128), nullable=False),
    sa.Column('tevv_run_id', sa.String(length=96), nullable=False),
    sa.Column('scenario_id', sa.String(length=32), nullable=False),
    sa.Column('repetition', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('expected', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('actual', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('case_id', sa.String(length=64), nullable=True),
    sa.Column('trace_id', sa.String(length=96), nullable=False),
    sa.Column('defect_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['tevv_run_id'], ['tevv_runs.tevv_run_id'], name=op.f('fk_tevv_results_tevv_run_id_tevv_runs')),
    sa.PrimaryKeyConstraint('tevv_result_id', name=op.f('pk_tevv_results')),
    sa.UniqueConstraint('tevv_run_id', 'scenario_id', 'repetition', name='uq_tevv_results_tevv_run_id')
    )
    op.create_table('uncertainty_records',
    sa.Column('uncertainty_id', sa.String(length=96), nullable=False),
    sa.Column('case_id', sa.String(length=64), nullable=False),
    sa.Column('kind', sa.String(length=32), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['case_id'], ['cases.case_id'], name=op.f('fk_uncertainty_records_case_id_cases')),
    sa.PrimaryKeyConstraint('uncertainty_id', name=op.f('pk_uncertainty_records'))
    )
    op.create_index('ix_uncertainty_records_case', 'uncertainty_records', ['case_id'], unique=False)
    op.create_table('claim_evidence_links',
    sa.Column('claim_evidence_link_id', sa.String(length=160), nullable=False),
    sa.Column('claim_id', sa.String(length=96), nullable=False),
    sa.Column('excerpt_id', sa.String(length=96), nullable=False),
    sa.Column('case_id', sa.String(length=64), nullable=False),
    sa.Column('quote_start', sa.Integer(), nullable=False),
    sa.Column('quote_end', sa.Integer(), nullable=False),
    sa.Column('quoted_text', sa.Text(), nullable=False),
    sa.Column('quote_verified', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['claim_id'], ['generated_claims.claim_id'], name=op.f('fk_claim_evidence_links_claim_id_generated_claims')),
    sa.ForeignKeyConstraint(['excerpt_id'], ['evidence_excerpts.excerpt_id'], name=op.f('fk_claim_evidence_links_excerpt_id_evidence_excerpts')),
    sa.PrimaryKeyConstraint('claim_evidence_link_id', name=op.f('pk_claim_evidence_links')),
    sa.UniqueConstraint('claim_id', 'excerpt_id', name='uq_claim_evidence_links_claim_id')
    )
    op.create_index(op.f('ix_claim_evidence_links_case_id'), 'claim_evidence_links', ['case_id'], unique=False)
    op.create_table('source_pages',
    sa.Column('source_page_id', sa.String(length=160), nullable=False),
    sa.Column('source_version_key', sa.String(length=128), nullable=False),
    sa.Column('page_number', sa.Integer(), nullable=False),
    sa.Column('section_headings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('char_start', sa.Integer(), nullable=False),
    sa.Column('char_end', sa.Integer(), nullable=False),
    sa.Column('block_count', sa.Integer(), nullable=False),
    sa.Column('page_text', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['source_version_key'], ['source_versions.source_version_key'], name=op.f('fk_source_pages_source_version_key_source_versions')),
    sa.PrimaryKeyConstraint('source_page_id', name=op.f('pk_source_pages')),
    sa.UniqueConstraint('source_version_key', 'page_number', name='uq_source_pages_source_version_key')
    )
    op.create_table('source_blocks',
    sa.Column('source_block_id', sa.String(length=160), nullable=False),
    sa.Column('source_page_id', sa.String(length=160), nullable=False),
    sa.Column('source_version_key', sa.String(length=128), nullable=False),
    sa.Column('block_index', sa.Integer(), nullable=False),
    sa.Column('page_number', sa.Integer(), nullable=False),
    sa.Column('section_heading', sa.Text(), nullable=False),
    sa.Column('char_start', sa.Integer(), nullable=False),
    sa.Column('char_end', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('text_sha256', sa.String(length=64), nullable=False),
    sa.Column('instruction_like_flags', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.ForeignKeyConstraint(['source_page_id'], ['source_pages.source_page_id'], name=op.f('fk_source_blocks_source_page_id_source_pages')),
    sa.ForeignKeyConstraint(['source_version_key'], ['source_versions.source_version_key'], name=op.f('fk_source_blocks_source_version_key_source_versions')),
    sa.PrimaryKeyConstraint('source_block_id', name=op.f('pk_source_blocks'))
    )
    op.create_index('ix_source_blocks_page', 'source_blocks', ['source_page_id'], unique=False)
    op.create_index('ix_source_blocks_version', 'source_blocks', ['source_version_key'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_source_blocks_version', table_name='source_blocks')
    op.drop_index('ix_source_blocks_page', table_name='source_blocks')
    op.drop_table('source_blocks')
    op.drop_table('source_pages')
    op.drop_index(op.f('ix_claim_evidence_links_case_id'), table_name='claim_evidence_links')
    op.drop_table('claim_evidence_links')
    op.drop_index('ix_uncertainty_records_case', table_name='uncertainty_records')
    op.drop_table('uncertainty_records')
    op.drop_table('tevv_results')
    op.drop_index('ix_source_versions_lifecycle', table_name='source_versions')
    op.drop_table('source_versions')
    op.drop_index(op.f('ix_model_runs_case_id'), table_name='model_runs')
    op.drop_table('model_runs')
    op.drop_index('uq_human_dispositions_final_per_packet', table_name='human_dispositions', postgresql_where=sa.text('is_final'), sqlite_where=sa.text('is_final = 1'))
    op.drop_index(op.f('ix_human_dispositions_case_id'), table_name='human_dispositions')
    op.drop_table('human_dispositions')
    op.drop_index(op.f('ix_generated_claims_case_id'), table_name='generated_claims')
    op.drop_table('generated_claims')
    op.drop_index('ix_evidence_excerpts_case', table_name='evidence_excerpts')
    op.drop_table('evidence_excerpts')
    op.drop_index('ix_deterministic_results_case', table_name='deterministic_results')
    op.drop_table('deterministic_results')
    op.drop_index(op.f('ix_demo_sessions_identity_id'), table_name='demo_sessions')
    op.drop_table('demo_sessions')
    op.drop_index('ix_decision_packets_case', table_name='decision_packets')
    op.drop_table('decision_packets')
    op.drop_index('ix_case_state_transitions_case', table_name='case_state_transitions')
    op.drop_table('case_state_transitions')
    op.drop_table('use_case_contracts')
    op.drop_table('tevv_runs')
    op.drop_table('status_records')
    op.drop_table('source_records')
    op.drop_table('model_configurations')
    op.drop_table('kill_switch_events')
    op.drop_table('evidence_records')
    op.drop_table('demo_identities')
    op.drop_table('defects')
    op.drop_index('ix_cases_state', table_name='cases')
    op.drop_index('ix_cases_requester', table_name='cases')
    op.drop_table('cases')
    op.drop_table('authorization_decisions')
    op.drop_index('ix_audit_events_type', table_name='audit_events')
    op.drop_index('ix_audit_events_case', table_name='audit_events')
    op.drop_table('audit_events')
