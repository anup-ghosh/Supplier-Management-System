def get_sender_mail(env):
    """
    Retrieve the sender email address from the mail server configuration.
    Args:env (Environment): The Odoo environment object.
    Returns:(str)The sender email address.
    """
    sender = env['ir.mail_server'].sudo().search([], order='sequence', limit=1)
    sender_mail = sender.smtp_user
    return sender_mail

def get_my_company(env):
    """
    Retrieve the name of the current company.
    Args:env (Environment): The Odoo environment object.
    Returns:(str)The name of the current company or "No Company Found" if no company is set.
    """
    sender = env['ir.mail_server'].sudo().search([], order='sequence', limit=1)
    current_company = env.company.name if env.company else "No Company Found"
    return current_company

def get_approvers_mail(env):
    """
    Retrieve the email addresses of users in the supplier management approver group.
    Args:env (Environment) The Odoo environment object.
    Returns:(str) A comma-separated string of approver email addresses.
    """
    group = env.ref('supplier_management.group_supplier_management_approver')
    approvers = env['res.users'].sudo().search(
        [('groups_id', 'in', group.id)])
    approver_mails = approvers.mapped('email')
    return ','.join(approver_mails)

def get_reviewers_mail(env):
    """
    Retrieve the email addresses of users in the supplier management reviewer group.
    Args:env (Environment) The Odoo environment object.
    Returns:(str)A comma-separated string of reviewer email addresses.
    """
    group = env.ref('supplier_management.group_supplier_management_reviewer')
    reviewers = env['res.users'].sudo().search(
        [('groups_id', 'in', group.id)])
    reviewer_mails = reviewers.mapped('email')
    return ','.join(reviewer_mails)

def get_suppliers_mail(env):
    """
    Retrieve the email addresses of users who are suppliers.
    Args:env (Environment) The Odoo environment object.
    Returns:(list)A list of supplier email addresses.
    """
    suppliers = env['res.users'].search([]).filtered(lambda u: u.partner_id and u.partner_id.supplier_rank > 0)
    supplier_mails = suppliers.mapped('login')
    return supplier_mails