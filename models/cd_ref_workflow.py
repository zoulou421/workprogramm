# -*- coding: utf-8 -*-
import logging
from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# --- MODÈLE workflow.hierarchy ---
class WorkflowHierarchy(models.Model):
    _name = 'workflow.hierarchy'
    _description = 'Gestion de la hiérarchie Domaine-Processus-Activité (Many2many)'

    name = fields.Char(string='Nom de l\'entrée hiérarchique', required=True, default='Nouvelle entrée')
    department_id = fields.Many2one('hr.department', string='Department')
    domain_ids = fields.Many2many('workflow.domain', string='Domaines')
    process_ids = fields.Many2many('workflow.process', string='Processus')
    sub_process_ids = fields.Many2many('workflow.subprocess', string='Sous-processus')
    activity_ids = fields.Many2many('workflow.activity', string='Activités')
    procedure_ids = fields.Many2many('workflow.procedure', string='Procédures')
    deliverable_ids = fields.Many2many('workflow.deliverable', string='Livrables')
    task_formulation_ids = fields.Many2many('workflow.task.formulation', string='Formulation de Tâches')
    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    project_id = fields.Many2one('qcproject.project', string='Project')
    allowed_department_ids = fields.Many2many(
        'hr.department',
        string="Départements autorisés",
        help="Sélectionnez les départements autorisés pour ce workflow."
    )

    @api.onchange('project_id')
    def _onchange_project_id(self):
        """
        Synchronise allowed_department_ids avec le project_type du projet sélectionné.
        """
        if self.project_id and self.project_id.project_type:
            department_ids = self.env['hr.department'].search([
                ('dpt_type', '=', self.project_id.project_type)
            ]).ids
            self.allowed_department_ids = [(6, 0, department_ids)]
        else:
            self.allowed_department_ids = [(5, 0, 0)]

    @api.onchange('allowed_department_ids')
    def _onchange_allowed_department_ids(self):
        """
        Synchronise department_id avec le premier département sélectionné dans allowed_department_ids.
        """
        if self.allowed_department_ids and not self.department_id:
            self.department_id = self.allowed_department_ids[0]

    @api.model
    def _find_or_create_m2m_records(self, model_name, field_name_in_row):
        """
        Helper pour trouver ou créer des enregistrements Many2many.
        """
        record_ids = []
        names_str = self.env.context.get(field_name_in_row)
        if not names_str:
            return [(5, 0, 0)]
        names = [name.strip() for name in names_str.split(',') if name.strip()]
        for name in names:
            record = self.env[model_name].search([('name', '=', name)], limit=1)
            if not record:
                _logger.info(f"Creating new {model_name}: {name}")
                try:
                    record = self.env[model_name].create({'name': name})
                except Exception as e:
                    _logger.error(f"Failed to create {model_name} '{name}': {e}", exc_info=True)
                    continue
            record_ids.append(record.id)
        return [(6, 0, record_ids)]

    @api.model
    def import_hierarchy(self, row):
        """
        Méthode pour importer ou mettre à jour une ligne de données avec des champs Many2many.
        """
        hierarchy_name = row.get('name', 'Nouvelle entrée')
        vals = {'name': hierarchy_name}
        try:
            vals['domain_ids'] = self.with_context(domain=row.get('domain'))._find_or_create_m2m_records(
                'workflow.domain', 'domain'
            )
            vals['process_ids'] = self.with_context(process=row.get('process'))._find_or_create_m2m_records(
                'workflow.process', 'process'
            )
            vals['sub_process_ids'] = self.with_context(sub_process=row.get('sub_process'))._find_or_create_m2m_records(
                'workflow.subprocess', 'sub_process'
            )
            vals['activity_ids'] = self.with_context(activity=row.get('activity'))._find_or_create_m2m_records(
                'workflow.activity', 'activity'
            )
            vals['procedure_ids'] = self.with_context(procedure=row.get('procedure'))._find_or_create_m2m_records(
                'workflow.procedure', 'procedure'
            )
            vals['deliverable_ids'] = self.with_context(deliverable=row.get('deliverable'))._find_or_create_m2m_records(
                'workflow.deliverable', 'deliverable'
            )
            vals['task_formulation_ids'] = self.with_context(
                task_formulation=row.get('task_formulation'))._find_or_create_m2m_records(
                'workflow.task.formulation', 'task_formulation'
            )
            if 'notes' in row:
                vals['notes'] = row['notes']
            vals['active'] = row.get('active', '1') == '1'

            existing_hierarchy_entry = self.search([('name', '=', hierarchy_name)], limit=1)
            if existing_hierarchy_entry:
                _logger.info(f"Updating existing workflow hierarchy entry: {hierarchy_name}")
                existing_hierarchy_entry.write(vals)
                return existing_hierarchy_entry
            else:
                _logger.info(f"Creating new workflow hierarchy entry: {hierarchy_name}")
                return self.create(vals)
        except Exception as e:
            _logger.error(f"Error importing workflow hierarchy row: {row}. Error: {e}", exc_info=True)
            return self.create({
                'name': f"ERREUR-IMPORT-{hierarchy_name}",
                'notes': f"Failed to import: {row}. Error: {e}",
                'active': False,
            })

# --- MODÈLE workflow.domain ---
class WorkflowDomain(models.Model):
    _name = 'workflow.domain'
    _description = 'Domaines de workflow (One2many vers processus)'
    name = fields.Char(string='Nom du domaine', required=True)
    dpt_type = fields.Selection(
        [('internal', 'Internal'), ('external', 'External')],
        string="Domain Type",
        default='internal',
        required=True,
        index=True,
        help="Specifies whether the domain is internal or external."
    )
    process_ids = fields.One2many('workflow.process', 'domain_id', string='Processus associés')
    #_sql_constraints = [('name_uniq', 'unique (name)', 'Le nom du domaine doit être unique !')]

# --- MODÈLE workflow.process ---
class WorkflowProcess(models.Model):
    _name = 'workflow.process'
    _description = 'Processus métier (One2many vers sous-processus, Many2one vers domaine)'

    name = fields.Char(string='Nom du processus', required=True)
    domain_id = fields.Many2one('workflow.domain', string='Domaine associé', ondelete='restrict')
    sub_process_ids = fields.One2many('workflow.subprocess', 'process_id', string='Sous-processus associés')
    #_sql_constraints = [('name_uniq', 'unique (name)', 'Le nom du processus doit être unique !')]

# --- MODÈLE workflow.subprocess ---
class WorkflowSubProcess(models.Model):
    _name = 'workflow.subprocess'
    _description = 'Sous-processus (One2many vers activités, Many2one vers processus)'
    name = fields.Char(string='Nom du sous-processus', required=True)
    process_id = fields.Many2one('workflow.process', string='Processus associé', ondelete='restrict')
    activity_ids = fields.One2many('workflow.activity', 'sub_process_id', string='Activités associées')
    #_sql_constraints = [('name_uniq', 'unique (name)', 'Le nom du sous-processus doit être unique !')]

# --- MODÈLE workflow.activity ---
class WorkflowActivity(models.Model):
    _name = 'workflow.activity'
    _description = 'Activités métier (One2many vers procédures et livrables, Many2one vers sous-processus)'
    name = fields.Char(string="Nom de l'activité", required=True)
    sub_process_id = fields.Many2one('workflow.subprocess', string='Sous-processus associé', ondelete='restrict')
    procedure_ids = fields.One2many('workflow.procedure', 'activity_id', string='Procédures associées')
    deliverable_ids = fields.One2many('workflow.deliverable', 'activity_id', string='Livrables associés')
    #_sql_constraints = [('name_uniq', 'unique (name)', 'Le nom de l\'activité doit être unique !')]

# --- MODÈLE workflow.procedure ---
class WorkflowProcedure(models.Model):
    _name = 'workflow.procedure'
    _description = 'Procédures de workflow (Many2one vers activité, One2many vers formulations de tâches)'
    name = fields.Char(string='Nom de la procédure', required=True)
    activity_id = fields.Many2one('workflow.activity', string='Activité associée', ondelete='restrict')
    task_formulation_ids = fields.One2many('workflow.task.formulation', 'procedure_id', string='Formulations de tâches associées')
    #_sql_constraints = [('name_uniq', 'unique (name)', 'Le nom de la procédure doit être unique !')]

# --- MODÈLE workflow.deliverable ---
class WorkflowDeliverable(models.Model):
    _name = 'workflow.deliverable'
    _description = 'Livrables de workflow (Many2one vers activité)'
    name = fields.Char(string='Nom du livrable', required=True)
    activity_id = fields.Many2one('workflow.activity', string='Activité associée', ondelete='restrict')
    #_sql_constraints = [('name_uniq', 'unique (name)', 'Le nom du livrable doit être unique !')]

# --- MODÈLE workflow.task.formulation ---
class WorkflowTaskFormulation(models.Model):
    _name = 'workflow.task.formulation'
    _description = 'Formulation des tâches (Many2one vers procédure)'
    name = fields.Char(string='Description de la tâche', required=True)
    procedure_id = fields.Many2one('workflow.procedure', string='Procédure associée', ondelete='restrict')
    #_sql_constraints = [('name_uniq', 'unique (name)', 'La description de la tâche doit être unique !')]