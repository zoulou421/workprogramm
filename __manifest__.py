# -*- coding: utf-8 -*-
{
    'name': "Work Program Management v.0",

    'summary': """
        Comprehensive workflow and work program management system with hierarchical structure""",

    'description': """
        Work Program Management Module
        =============================

        This module provides a complete solution for managing workflows and work programs with:

        * Hierarchical workflow structure (Domain > Process > Subprocess > Activity > Procedure)
        * Work program planning and tracking
        * Department-based access control
        * Task formulation and deliverable management
        * Integration with HR departments

        Key Features:
        * Multi-level workflow hierarchy
        * Role-based permissions (User/Manager/Administrator)
        * Department-specific access rules
        * Work program scheduling and monitoring
    """,

    'author': "Your Company Name",
    'website': "https://www.yourcompany.com",

    'category': 'Project',  # Plus approprié que 'Uncategorized'
    'version': '1.0.0',

    # Dépendances nécessaires
    'depends': [
        'base',
        'web',
        'project',
        'mail',
        'hr',
        'website'
    ],

    # Fichiers de données - ordre important !
    'data': [
        # Sécurité en premier
        'security/security.xml',

        # Vues et actions
        'views/views.xml',
        'views/work_actions.xml',
        'views/work_menus.xml',
        'views/cd_ref_workflow.xml',
        'views/work_program_view.xml',
        'views/hr_department_view.xml',
        # Templates en dernier
        'views/templates.xml',
        'views/work_program_layout_controller.xml',
    ],

    # Données de démonstration
    'demo': [
        'demo/demo.xml',
    ],

    # Assets web (si nécessaire)
    'assets': {
        'web.assets_backend': [
            # 'workprogramm/static/src/css/workprogramm.css',
            # 'workprogramm/static/src/js/workprogramm.js',
        ],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'sequence': 10,
}