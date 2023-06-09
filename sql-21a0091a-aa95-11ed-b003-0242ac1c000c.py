# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
from tools.translate import _
import time

class pos_open_statement(osv.osv_memory):
    _name = 'pos.open.statement'
    _description = 'Open Statements'

    def open_statement(self, cr, uid, ids, context):
        """
             Open the statements
             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param context: A standard dictionary
             @return : Blank Directory
        """
        list_statement = []
        mod_obj = self.pool.get('ir.model.data')
        company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
        statement_obj = self.pool.get('account.bank.statement')
        sequence_obj = self.pool.get('ir.sequence')
        journal_obj = self.pool.get('account.journal')
        cr.execute("""select DISTINCT journal_id from pos_journal_users where user_id=%d order by journal_id"""%(uid))
        j_ids = map(lambda x1: x1[0], cr.fetchall())
        cr.execute(""" select id from account_journal
                            where auto_cash='True' and type='cash'
                            and id in (%s)""" %(','.join(map(lambda x: "'" + str(x) + "'", j_ids))))
        journal_ids = map(lambda x1: x1[0], cr.fetchall())

        for journal in journal_obj.browse(cr, uid, journal_ids):
            ids = statement_obj.search(cr, uid, [('state', '!=', 'confirm'), ('user_id', '=', uid), ('journal_id', '=', journal.id)])
            if len(ids):
                raise osv.except_osv(_('Message'), _('You can not open a Cashbox for "%s". \n Please close the cashbox related to. ' %(journal.name)))
            
#            cr.execute(""" Select id from account_bank_statement
#                                    where journal_id =%d
#                                    and company_id =%d
#                                    order by id desc limit 1""" %(journal.id, company_id))
#            st_id = cr.fetchone()
            
            number = ''
            if journal.sequence_id:
                number = sequence_obj.get_id(cr, uid, journal.sequence_id.id)
            else:
                number = sequence_obj.get(cr, uid, 'account.bank.statement')
            
            statement_id = statement_obj.create(cr, uid, {'journal_id': journal.id,
                                                          'company_id': company_id,
                                                          'user_id': uid,
                                                          'state': 'open',
                                                          'name': number,
                                                          'starting_details_ids': statement_obj._get_cash_close_box_lines(cr, uid, []),
                                                      })
            statement_obj.button_open(cr, uid, [statement_id], context)

    #            period = statement_obj._get_period(cr, uid, context) or None
    #            cr.execute("INSERT INTO account_bank_statement(journal_id,company_id,user_id,state,name, period_id,date) VALUES(%d,%d,%d,'open','%s',%d,'%s')"%(journal.id, company_id, uid, number, period, time.strftime('%Y-%m-%d %H:%M:%S')))
    #            cr.commit()
    #            cr.execute("select id from account_bank_statement where journal_id=%d and company_id=%d and user_id=%d and state='open' and name='%s'"%(journal.id, company_id, uid, number))
    #            statement_id = cr.fetchone()[0]
    #            print "statement_id",statement_id
    #            if st_id:
    #                statemt_id = statement_obj.browse(cr, uid, st_id[0])
    #                list_statement.append(statemt_id.id)
    #                if statemt_id and statemt_id.ending_details_ids:
    #                    statement_obj.write(cr, uid, [statement_id], {
    #                        'balance_start': statemt_id.balance_end,
    #                        'state': 'open',
    #                    })
    #                    if statemt_id.ending_details_ids:
    #                        for i in statemt_id.ending_details_ids:
    #                            c = statement_obj.create(cr, uid, {
    #                                'pieces': i.pieces,
    #                                'number': i.number,
    #                                'starting_id': statement_id,
    #                            })
        data_obj = self.pool.get('ir.model.data')
        id2 = data_obj._get_id(cr, uid, 'account', 'view_bank_statement_tree')
        id3 = data_obj._get_id(cr, uid, 'account', 'view_bank_statement_form2')
        if id2:
            id2 = data_obj.browse(cr, uid, id2, context=context).res_id
        if id3:
            id3 = data_obj.browse(cr, uid, id3, context=context).res_id

        return {
#           'domain': "[('id','in', ["+','.join(map(str,list_statement))+"])]",
            'domain': "[('state','=','open')]",
            'name': 'Open Statement',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.bank.statement',
            'views': [(id2, 'tree'),(id3, 'form')],
            'type': 'ir.actions.act_window'
}
pos_open_statement()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
