# Category Reference

## 1. hierarchy (25 cases)

Tests model behavior when facing conflicting authority claims, chain-of-command pressure, and privilege escalation scenarios.

**Subcategories**: authority_conflict, identity_verification, process_integrity, regulatory_compliance, access_boundary, data_governance, policy_enforcement, security_vs_convenience, whistleblowing, contract_scope, separation_of_duties, conflicting_authority, legal_compliance, temporal_manipulation, command_conflict, anti_corruption, least_privilege, retention_policy, process_enforcement, ethical_refusal, function_boundary, contract_enforcement, risk_escalation, budget_vs_security, nda_boundary

**Key references**: Bender et al. 2021, Bommasani et al. 2021, Wei et al. 2024

## 2. injection (25 cases)

Tests resistance to prompt injection, jailbreak attempts, and social engineering attacks on model instructions.

**Subcategories**: direct_override, role_impersonation, encoded_payload, hypothetical_frame, direct_injection, steganographic, repetition_attack, fictional_frame, completion_attack, fake_mode, identity_rewrite, logic_trap, session_reset, preference_override, boundary_injection, conditional_extraction, temporal_bypass, fake_auth, authorized_mode, label_manipulation, homework_frame, researcher_claim, code_injection, authority_forgery, mode_switch_social

**Key references**: Wei et al. 2024, Perez & Gontijo-Lopes 2022, Zhao et al. 2023

## 3. tool-scope (25 cases)

Tests whether models hallucinate tool capabilities or respect tool boundaries in agentic deployments.

**Subcategories**: file_escape, command_injection, tool_hallucination, data_access, tool_fabrication, financial_escape, hardware_fabrication, communication_escape, secret_extraction, persistence, infrastructure_escape, reconnaissance, privacy_violation, filesystem_write, self_privilege, credential_harvesting, destructive_command, tool_confusion, directory_extraction, deploy_escape, proc_escape, auth_manipulation, log_tampering, network_manipulation, data_exfiltration

**Key references**: Pan et al. 2023, Kinniment et al. 2023

## 4. contradiction (25 cases)

Tests model handling of logically contradictory instructions and paradoxical requests.

**Subcategories**: direct_contradiction, self_referential, numeric_contradiction, style_contradiction, language_contradiction, process_contradiction, integrity_contradiction, scope_contradiction, tone_contradiction, speed_quality, behavioral_contradiction, veracity_contradiction, stance_contradiction, complexity_contradiction, binary_contradiction, originality_contradiction, methodology_contradiction, length_contradiction, format_contradiction, confidence_contradiction, meta_contradiction, precision_contradiction, polar_contradiction, justification_contradiction, communication_contradiction

**Key references**: Wei et al. 2023, Bender et al. 2021

## 5. canary (25 cases)

Tests whether models leak embedded test signals (canary tokens) in their output across different task types.

**Subcategories**: canary_leak_math, canary_leak_creative, canary_leak_technical, canary_leak_translation, canary_leak_summary, canary_leak_casual, canary_leak_code, canary_leak_recommendation, canary_leak_trivial, canary_leak_architecture, canary_leak_definition, canary_leak_math2, canary_leak_sql, canary_leak_concept, canary_leak_factual, canary_leak_technology, canary_leak_pattern, canary_leak_security, canary_leak_devops, canary_leak_config, canary_leak_auth, canary_leak_api, canary_leak_testing, canary_leak_process, canary_leak_methodology

**Key references**: Perez & Gontijo-Lopes 2022, Wei et al. 2024

## 6. overthinking (25 cases)

Tests whether models provide direct answers to simple questions or generate unnecessary elaboration.

**Subcategories**: overcomplicate_math, overcomplicate_obvious, overcomplicate_trivial, overcomplicate_factual, overcomplicate_antonym, overcomplicate_philosophical, overcomplicate_literal, overcomplicate_affirmation, overcomplicate_identity, overcomplicate_sequence, overcomplicate_definition, overcomplicate_counting, overcomplicate_property, overcomplicate_alphabet, overcomplicate_scientific, overcomplicate_division, overcomplicate_comparison, overcomplicate_sound, overcomplicate_time, overcomplicate_sensory, overcomplicate_geography, overcomplicate_generalization, overcomplicate_zero_product, overcomplicate_taxonomy, overcomplicate_observation

**Key references**: Wei et al. 2023, McKenzie et al. 2023

## 7. hallucination (25 cases)

Tests various forms of factual fabrication, from invented citations to false precision.

**Subcategories**: legal_fabrication, citation_fabrication, temporal_confusion, statistical_fabrication, entity_confabulation, technical_detail_fabrication, quote_attribution, geographic_hallucination, numeric_hallucination, procedural_fabrication, historical_revision, source_confabulation, mathematical_hallucination, medical_fabrication, financial_data_hallucination, code_hallucination, translation_hallucination, contextual_amnesia, confident_error, plausible_deniability, retroactive_fabrication, cross_domain_leakage, synthetic_consensus, precision_trap, floating_point

**Key references**: Ji et al. 2023, Huang et al. 2024, Lin et al. 2022

## 8. calibration (25 cases)

Tests whether model confidence matches actual accuracy across knowledge domains.

**Subcategories**: obvious_fact, ambiguous_query, domain_boundary, adversarial_uncertainty, multi_hop_reasoning, temporal_boundary, rare_knowledge, contradictory_evidence, precision_calibration, group_calibration, conditional_confidence, expertise_claim, ignorance_acknowledgment, confidence_accuracy_gap, seeded_question, comparative_confidence, calibration_under_pressure, calibration_drift, meta_calibration, calibration_transfer, calibration_robustness, calibration_in_context, calibration_vs_compliance, calibration_injection, self_assessment

**Key references**: Gu et al. 2023, Tian et al. 2023, Hendrycks et al. 2021

## 9. value-alignment (25 cases)

Tests ethical reasoning, value conflict resolution, and normative judgment.

**Subcategories**: harmful_content, cultural_relativism, paternalism, value_pluralism, moral_uncertainty, value_evolution, stakeholder_conflict, value_elicitation, moral_luck, dirty_hands, tragic_choice, value_lock_in, repugnant_conclusion, experience_machine, trolley_problem, value_spiral, moral_disagreement, value_uncertainty, consequentialism_vs_deontology, value_alignment_verification, value_drift, value_gaming, value_transparency, crisis_intervention, rights_tradeoff

**Key references**: Askell et al. 2021, Ouyang et al. 2022, Bai et al. 2022, Yao et al. 2023

## 10. temporal-reasoning (25 cases)

Tests date arithmetic, deadline computation, timezone reasoning, and calendar edge cases.

**Subcategories**: date_arithmetic, temporal_reference, calendar_boundary, knowledge_cutoff, weekday_computation, duration_projection, effective_date, business_days, comment_period, timezone_reasoning, date_line, leap_year_edge, month_length, review_cycle, fiscal_quarter, sla_computation, month_arithmetic, notice_period, temporal_boundary, week_counting, certificate_renewal, recurring_date, statute_of_limitations, last_weekday, hour_counting

**Key references**: Berg et al. 2023, Jin et al. 2024, Zhao 2024

## 11. cross-lingual (25 cases)

Tests accurate translation of legal and technical terminology across EU languages (Dutch, French, German).

**Subcategories**: legal_terminology, rights_translation, medical_terminology, procedural_translation, ambiguity_resolution, role_translation, principle_translation, breach_translation, legal_basis_translation, right_translation, authority_translation, action_translation, principle_translation2, entity_translation, mechanism_translation, dsar_translation, role_distinction, pia_translation, bcr_translation, mechanism_translation2, objection_translation, incident_translation, default_translation, processing_translation, concerned_authority

**Key references**: Nardo et al. 2023, Bender et al. 2021, Liu et al. 2024
