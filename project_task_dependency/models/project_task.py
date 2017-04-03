# -*- coding: utf-8 -*-
# © 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.exceptions import Warning


class ProjectTask(models.Model):
    _inherit = 'project.task'

    dependency_task_ids = fields.Many2many(
        string='Dependencies',
        comodel_name='project.task',
        relation='project_task_dependency_task_rel',
        column1='task_id', column2='dependency_task_id'
    )

    recursive_dependency_task_ids = fields.Many2many(
        string='Recursive Dependencies',
        comodel_name='project.task',
        compute='_compute_dependency'
    )

    depending_task_ids = fields.Many2many(
        string='Depending Tasks',
        comodel_name='project.task',
        help='Tasks that are dependent on this task.',
        compute='_compute_dependency'
    )

    recursive_depending_task_ids = fields.Many2many(
        string='Recursive Depending Tasks',
        comodel_name='project.task',
        help='Tasks that are dependent on this task (recursive).',
        compute='_compute_dependency'
    )

    @api.one
    @api.depends('dependency_task_ids')
    def _compute_dependency(self):
        self.recursive_dependency_task_ids = self.get_dependency_tasks(self,
                                                                       True)
        self.depending_task_ids = self.get_depending_tasks(self)
        self.recursive_depending_task_ids = self.get_depending_tasks(self,
                                                                     True)

    @api.model
    def get_dependency_tasks(self, task, recursive=False):
        dependency_tasks = task.dependency_task_ids
        if recursive:
            for t in dependency_tasks:
                dependency_tasks += self.get_dependency_tasks(t, recursive)
        return dependency_tasks

    @api.model
    def get_depending_tasks(self, task, recursive=False):
        if not isinstance(task.id, models.NewId):
            depending_tasks = self.search([(
                'dependency_task_ids', 'in', task.id)
            ])
            if recursive:
                for t in depending_tasks:
                    depending_tasks += self.get_depending_tasks(t, recursive)
            return depending_tasks

    @api.multi
    def write(self, vals):
        stage_id = vals.get('stage_id', False)
        if stage_id and self.dependency_task_ids:
            stage_model = self.env['project.task.type']
            stage = stage_model.browse(stage_id)
            if stage.closed:
                for task in self.dependency_task_ids:
                    if not task.stage_id.closed:
                        raise Warning('The task depends on: %s' % task.name)
        if stage_id and self.depending_task_ids:
            stage_model = self.env['project.task.type']
            stage = stage_model.browse(stage_id)
            if not stage.closed:
                for task in self.depending_task_ids:
                    if task.stage_id.closed:
                        raise Warning(
                            'The task is a dependency of: %s' % task.name)

        return super(ProjectTask, self).write(vals)


