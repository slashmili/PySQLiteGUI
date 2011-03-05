#!/usr/bin/env python

# pySQLiteGUI - An SQLite database admin tool
# This application is free software; you can redistribute
# it and/or modify it under the terms of the Ruby license
# defined in the COPYING file

#Copyright (c) 2007 Milad Rastian. All rights reserved.



__authors__ = "Milad Rastian <milad[at]rastian.com>"
__copyright__ = "Copyright (C) 2007 Milad Rastian "
__revision__ = "$Id$"
__version__ = "0.0.8RC0"
__license__="GPL"

import os
#os.environ['LANG']="fa_IR.UTF-8"
import pygtk
pygtk.require("2.0")
import gtk
import gtk.glade
from pysqlite2 import dbapi2 as sqlite
import gobject

ERRORS={
        101:['DB Error','Its not a valid SQLite Database'],
        102:['Empty Entry Error','Please enter field name'],
        103:['Empty Entry Error','Please select data type'],
        104:['Empty Entry Error','The field size of VARCHAR and NVARCHAR is required'],
        105:['I/O Error','The destination file already exists.\nDo you want to overwrite it?'],
        106:['I/O Error',"Not enough permissions to write into the file"],
        107:['Entry Error','The filed name already exists'],
        108:['SQL Action','Are you sure you want to delete table?'],
        109:['','Please select a table'],
        110:['Empty Entry Error','Please enter the table name'],
        111:['SQL Error','Only one field could be attributed as Auto Increment'],
        112:['SQL Error',''],
        113:['DB Error','No Database is selected'],
        114:['DB Error','There is already another table or index with this name'],
        115:['Close Database','Are you sure close database ? ']
        }

dataTypes=['Integer','Real','Number','Boolean','Time','Date','Timestamp','Varchar','Nvarchar','Text','Blob']



 
class pSqliteGUI:
    def __init__(self):
        self.file_name=""
        self.con=None
        self.cur=None
        self.sql_history=""
        self.dir_history=""
        self.last_filed_number=0
        self.edit_field=None
        self.edit_table=None
        self.wTree=gtk.glade.XML("psqlitegui.glade")
        self.main_window = self.wTree.get_widget("pysqlite")
        
        self.tables_store = gtk.ListStore(str)
        self.tables=self.wTree.get_widget("tables")
        self.tables.set_model(self.tables_store)
        self.tables.set_search_column(0)
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn("Table(s)",cell,text=0)
        self.tables.append_column(col)
        
        self.db_table=self.wTree.get_widget("table")
        self.tbl_rows=None
        
        self.columns=self.wTree.get_widget("columns")
        self.main_window.connect("destroy",gtk.main_quit)
        
        self.TableWindow=None
        
    def show_msg(self,key,icon="error",buttons="close"):
        """Show message dialog"""
        msgicon=0
        msgbuttons=0
        if icon=="error":
            msgicon=gtk.MESSAGE_ERROR
        elif icon=="info":
            msgicon=gtk.MESSAGE_INFO
        elif icon=="question":
            msgicon=gtk.MESSAGE_QUESTION
        elif icon=="warning":
            msgicon=gtk.MESSAGE_WARNING
            
        if buttons=="close":
            msgbuttons=gtk.BUTTONS_CLOSE
        elif buttons=="yesno":
            msgbuttons=gtk.BUTTONS_YES_NO
 
        msgWindow=gtk.MessageDialog(None,0,msgicon,msgbuttons,ERRORS[key][0] )
            
        msgWindow.format_secondary_text(ERRORS[key][1])
        response=msgWindow.run()
        msgWindow.destroy()
        return response
        

        
    def find_index(self,array,find):
        """find index of find in array"""
        index=0
        for fnd in array:
            if fnd==find:
                return index
            index+=1
        return -1


    def set_database_sensitive(self,state):
        """change sensitive object after open or close database"""
        self.wTree.get_widget("tool_save_as").set_sensitive(state)
        self.wTree.get_widget("tool_close").set_sensitive(state)
        self.wTree.get_widget("tool_refresh").set_sensitive(state)
        self.wTree.get_widget("drop_table").set_sensitive(state)
        self.wTree.get_widget("rename_table").set_sensitive(state)
        self.wTree.get_widget("add_table").set_sensitive(state)
        self.wTree.get_widget("tool_execute_sql").set_sensitive(state)
        if state==False:
            self.sql_history=""
    
    def set_table_sensitive(self,state):
        """change sensitive object after load or unload table"""
        self.wTree.get_widget("tool_paste_row").set_sensitive(state)
        self.wTree.get_widget("tool_edit_row").set_sensitive(state)
        self.wTree.get_widget("tool_remove_row").set_sensitive(state)
        self.wTree.get_widget("tool_add_row").set_sensitive(state)
        self.wTree.get_widget("tool_copy_row").set_sensitive(state)
        
    def create_database(self,filename):       
        """create database file"""
        try : 
            file_handler=open(filename,'w+')
            self.file_name=filename
            self.main_window.set_title('pySQLiteGUI('+filename+')')
            self.set_database_sensitive(True)
        except IOError:
            self.show_msg(106)
            return 
    def copy_database(self,filename): 
        """copy (Sava as database)"""
        try : 
            buff=open(self.file_name , 'r').read() 
            file = open(filename, 'w+') 
            file.write(buff)
            file.close()
            self.file_name=filename
            self.con = None
            self.cur = None     
            self.load_tables()
        except IOError:
            self.show_msg(106)
            return    
                
class pSqliteGUIActions(pSqliteGUI):
     def __init__(self):
         pSqliteGUI.__init__(self)
         self.connect_object()
         self.main_window.show()
         #insert data types into GtkComboBox
         column_type=self.wTree.get_widget("column_type")
         for type in dataTypes:
             column_type.append_text(type)
             
     def connect_object(self):
        mdict={"new_database":self.new_database,
               "open_database":self.open_database,
               "select_table":self.select_table,
               "add_table":self.add_table,
               "hide_table_view":self.hide_table_view,
               "add_column":self.add_column,
               "primarykey_clicked":self.primarykey_clicked,
               "autoincrement_clicked":self.autoincrement_clicked,
               "remove_column":self.remove_column,
               "edit_column":self.edit_column,
               "drop_table":self.drop_table,
               "rename_table":self.rename_table,
               "apply_changes":self.apply_changes,
               "close_database":self.close_database,
               "save_database_as":self.save_database_as,
               "execute_sql":self.execute_sql,
               "refresh_date":self.select_table,
               "about_tool":self.about
               }  
        self.wTree.signal_autoconnect(mdict) 
         
     
     def open_database(self,widget):
        # self.file_name="/home/jandark/workspace/psqlitegui/test/test.db"
         #self.load_tables()
         #return
         dialog = gtk.FileChooserDialog("Open Database",
                                        None,
                                        gtk.FILE_CHOOSER_ACTION_OPEN,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OPEN, gtk.RESPONSE_OK))
         dialog.set_default_response(gtk.RESPONSE_OK)
         response = dialog.run()
        

         if response == gtk.RESPONSE_OK:
             self.close_database("")
             self.file_name=dialog.get_filename()
             self.load_tables()
             
             
         dialog.destroy()    
         
         
         
     def new_database(self,widget):
        dialog = gtk.FileChooserDialog("New Database ",
                                     None,
                                     gtk.FILE_CHOOSER_ACTION_SAVE,
                                     (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                      gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)

        filter = gtk.FileFilter()
        filter.set_name("SQLite2")
        filter.add_pattern("*")
        dialog.add_filter(filter)
        filter = gtk.FileFilter()
        filter.set_name("SQLite3")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            filename=dialog.get_filename()
            dialog.destroy()
            if os.path.exists(filename) ==True:
                if self.show_msg(105, "info","yesno")==gtk.RESPONSE_YES:
                    
                    self.create_database(filename)
                    
            else:
                self.create_database(filename)
            
        else:
            dialog.destroy()
                
              

         
     def close_database(self,widget):
         """Close Database"""
         if widget!="":
             if self.show_msg(115, "question", "yesno")==gtk.RESPONSE_YES:
                 self.main_window.set_title('pySQLiteGUI')
                 self.set_database_sensitive(False)
                 self.set_table_sensitive(False) 
                 for col in self.db_table.get_columns() :
                     self.db_table.remove_column(col)
                 self.con=None
                 self.cur=None
                 self.file_name=None
                 self.tables_store.clear()
     
     def save_database_as(self,widget):
        """sava as databases """
        dialog = gtk.FileChooserDialog("Save As Database ... ",
                                     None,
                                     gtk.FILE_CHOOSER_ACTION_SAVE,
                                     (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                      gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)

        filter = gtk.FileFilter()
        filter.set_name("SQLite2")
        filter.add_pattern("*")
        dialog.add_filter(filter)
        filter = gtk.FileFilter()
        filter.set_name("SQLite3")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            filename=dialog.get_filename()
            dialog.destroy()
            if os.path.exists(filename) ==True:
                if self.show_msg(105, "info","yesno")==gtk.RESPONSE_YES:
                    
                    #self.create_database(filename)
                    self.copy_database(filename)
                    
            else:
                self.copy_database(filename)
                pass
            
        else:
            dialog.destroy()
    
     def load_tables(self):
         """load databases and fill table in treeview"""
         self.con = sqlite.connect(self.file_name)
         self.cur = self.con.cursor()
         try:
             self.cur.execute("Select Name FROM sqlite_master WHERE type='table' ORDER BY Name")
             self.main_window.set_title('pySQLiteGUI('+self.file_name+')')
             self.set_database_sensitive(True)
         except sqlite.DatabaseError:
             self.show_msg(101)
             self.con=None
             self.cur=None
             self.file_name=None
             return
         rows=self.cur.fetchall()
         #self.cur.execute("insert into fred2 values ('F','hmmsmm','s3432tone','br243ead?')")
         self.tables_store.clear()
         for tbl in rows:
             self.tables_store.append([tbl[0]])
       
       
     def clear_db_table(self):
         self.tbl_rows.clear()
         #remove Last columns from db_table TreeView
         for col in self.db_table.get_columns() :
             self.db_table.remove_column(col)         
         
     def select_table(self,widget):   
         """select table event, browse table selected"""
         selection=self.tables.get_selection()
         (mode,iter)=selection.get_selected()
         if iter:
             table=mode.get(iter,0)[0]
             try:
                 self.cur.execute("Select * FROM %s"%(table))
                 
                 #remove Last columns from db_table TreeView
                 for col in self.db_table.get_columns() :
                     self.db_table.remove_column(col)
                  
                 list=[]
                 for i in (self.cur.description):
                     list.append(gobject.TYPE_STRING)

                 t = tuple(list)
                 
                 self.tbl_rows = gtk.ListStore(*t)
                 cell = gtk.CellRendererText()
                 index=0
                 for fieldDesc in self.cur.description:
                     col = gtk.TreeViewColumn(fieldDesc[0],cell,text=index)
                     self.db_table.append_column(col)
                     self.db_table.get_column(index).set_resizable(True)
                     index+=1
                     
                     
                 self.db_table.set_model(self.tbl_rows)
                 rows=self.cur.fetchall()
                 for rcd in rows:
                     self.tbl_rows.append(rcd)
                     
                 self.set_table_sensitive(True)  
             except sqlite.OperationalError , errormsg:
                 ERRORS[112][1]=errormsg.__str__()
                 self.show_msg(112)
                 mode.remove(iter)
                 self.clear_db_table()
                 
             #print self.cur.description()
             
     def add_table(self,widget):
         """show table_view window"""
         #self.wTree2=gtk.glade.XML("psqlitegui.glade","table_view")
         
         #self.TableWindow = self.wTree2.get_widget("table_view")
         #dict={"destroy":self.TableWindow.destroy }
         #self.wTree2.signal_autoconnect(dict)
           
         self.TableWindow = self.wTree.get_widget("table_view")
         #dict={"destroy":self.TableWindow.destroy }
         #self.wTree2.signal_autoconnect(dict)
         

         
         self.TableWindow.connect("destroy",self.hide_table_view)
         
         
         for col in self.columns.get_columns() :
             self.columns.remove_column(col)
             
             
         cell = gtk.CellRendererText()
         self.tbl_columns_rows = gtk.ListStore(gobject.TYPE_STRING,
                                               gobject.TYPE_STRING,
                                               gobject.TYPE_STRING,
                                               gobject.TYPE_STRING,
                                               gobject.TYPE_STRING,
                                               gobject.TYPE_STRING,
                                               gobject.TYPE_STRING)
         
         col = gtk.TreeViewColumn("Name",cell,text=0)
         col.set_resizable(True)
         self.columns.append_column(col)

         col = gtk.TreeViewColumn("Type",cell,text=1)
         col.set_resizable(True)
         self.columns.append_column(col)

         col = gtk.TreeViewColumn("Size",cell,text=2)
         col.set_resizable(True)
         self.columns.append_column(col)
         
         col = gtk.TreeViewColumn("Value",cell,text=3)
         col.set_resizable(True)
         self.columns.append_column(col)

         col = gtk.TreeViewColumn("Constraint",cell,text=4)
         col.set_resizable(True)
         self.columns.append_column(col)
         
         self.columns.set_model(self.tbl_columns_rows)
         
         #self.TableWindow.set_transient_for(self.main_window)
         self.TableWindow.show()
         
         self.last_filed_number=0
         
     def hide_table_view(self,widget,w=None):
         """hide table_view window"""
         print widget
         print w
         
         self.clear_form()
         self.TableWindow.hide()
         #self.TableWindow=widget
     def add_column(self,widget):
         
         error=False
         new_row=[]
         column_name=self.wTree.get_widget("column_name")
         if column_name.get_text()=='': 
             self.show_msg(102)
             column_name.grab_focus()
             return
         new_row.append(column_name.get_text())         
         
         column_type=self.wTree.get_widget("column_type")
         if column_type.get_active()==-1 : 
             self.show_msg(103)
             column_type.grab_focus()
             return 
         new_row.append(dataTypes[column_type.get_active()])

         column_size=self.wTree.get_widget("column_size")
         new_row.append(column_size.get_text())
         if column_size.get_text()=='' and (column_type.get_active()==self.find_index(dataTypes,'Varchar') or  column_type.get_active()==self.find_index(dataTypes,'Nvarchar') ): 
             self.show_msg(104)
             column_size.grab_focus()
             return 

         column_default=self.wTree.get_widget("column_default")
         new_row.append(column_default.get_text())

         column_primarykey=self.wTree.get_widget("column_primarykey")
         column_autoincrement=self.wTree.get_widget("column_autoincrement")
         column_unique=self.wTree.get_widget("column_unique")
         column_notnull=self.wTree.get_widget("column_notnull")  
         
         constraint_test=''
         constraint_value=''
         
         if column_unique.get_active()==True: 
             constraint_test+='UNIQUE '
             constraint_value+='UNIQUE'
        
         if column_notnull.get_active()==True: 
             constraint_test+='NOT NULL '
             constraint_value+=',NOT NULL'
             
         if column_primarykey.get_active()==True: 
             constraint_test+='PRIMARY KEY '
             constraint_value+=',PRIMARY KEY'             
         
         new_row.append(constraint_test)
         new_row.append(constraint_value)
         
         
         if self.edit_field==None:
             new_row.append(self.last_filed_number)
             check_col=self.check_columns(new_row)
             if check_col==0:
                 self.tbl_columns_rows.append(new_row)
                 self.last_filed_number+=1
             else:
                 self.show_msg(check_col)
                 return
         else :
             new_row.append(self.edit_id)
             check_col=self.check_columns(new_row)
             if check_col==0:
                 self.tbl_columns_rows.set(self.edit_field,0,new_row[0])
                 self.tbl_columns_rows.set(self.edit_field,1,new_row[1])
                 self.tbl_columns_rows.set(self.edit_field,2,new_row[2])
                 self.tbl_columns_rows.set(self.edit_field,3,new_row[3])
                 self.tbl_columns_rows.set(self.edit_field,4,new_row[4])
                 self.tbl_columns_rows.set(self.edit_field,5,new_row[5])
                 
             else:
                 self.show_msg(check_col)
                 return                 
             self.edit_field=None
             self.edit_id=None
         column_name.grab_focus()
         self.clear_form()
         
     def clear_form(self):
         """Empty form"""
         column_name=self.wTree.get_widget("column_name")
         column_name.set_text('')

         table_name=self.wTree.get_widget("table_name")
         table_name.set_text('')
                  
         

         extra_table_options=self.wTree.get_widget("extra_table_options")
         extra_table_options.set_text('')
         
         column_type=self.wTree.get_widget("column_type")
         column_type.set_active(-1)
         
         column_size=self.wTree.get_widget("column_size")
         column_size.set_text('')
         
         column_default=self.wTree.get_widget("column_default")
         column_default.set_text('')
         
         column_primarykey=self.wTree.get_widget("column_primarykey")
         column_primarykey.set_active(False)
         column_primarykey.set_sensitive(True)
         
         column_autoincrement=self.wTree.get_widget("column_autoincrement")
         column_autoincrement.set_active(False)
         column_autoincrement.set_sensitive(True)
         
         column_unique=self.wTree.get_widget("column_unique")
         column_unique.set_active(False)
         column_unique.set_sensitive(True)
         
         column_notnull=self.wTree.get_widget("column_notnull")         
         column_notnull.set_active(False)
         column_notnull.set_sensitive(True)
         
         
     def primarykey_clicked(self,widget):    
         """Event when column_primarykey clicked"""
         column_primarykey=self.wTree.get_widget("column_primarykey")
         column_unique=self.wTree.get_widget("column_unique")
         column_notnull=self.wTree.get_widget("column_notnull")
         
         if column_primarykey.get_active()==True:
             column_notnull.set_active(True)
             column_notnull.set_sensitive(False)
             column_unique.set_sensitive(False)
         else:
             column_notnull.set_active(False)
             column_notnull.set_sensitive(True)
             column_unique.set_sensitive(True)
      
      
     def autoincrement_clicked(self,wdiget):   
         """Event when column_autoincrement clicked"""
         column_primarykey=self.wTree.get_widget("column_primarykey")
         column_autoincrement=self.wTree.get_widget("column_autoincrement")
         column_unique=self.wTree.get_widget("column_unique")
         column_notnull=self.wTree.get_widget("column_notnull")         
         column_type=self.wTree.get_widget("column_type") 
         
         if column_autoincrement.get_active()==True:
             column_primarykey.set_active(True)
             column_primarykey.set_sensitive(False)
             column_notnull.set_active(True)
             column_notnull.set_sensitive(False)   
             column_unique.set_sensitive(False)    
             column_type.set_active(0)                   
             column_type.set_sensitive(False)    
         else:
             column_primarykey.set_active(False)
             column_primarykey.set_sensitive(True)
             column_notnull.set_active(False)
             column_notnull.set_sensitive(True)   
             column_unique.set_sensitive(True) 
             column_unique.set_active(False)
             column_type.set_sensitive(True)        
     def remove_column(self,widget):
         """Remove filed row in table view """
         selection=self.columns.get_selection()
         (mode,iter)=selection.get_selected()
         if iter:
             mode.remove(iter)
             #self.columns.remove_column(selection.get_selected())
             self.columns.grab_focus()
     
     def edit_column(self,widget):   
         self.clear_form()
         """Edit field row in table view"""
         selection=self.columns.get_selection()
         (mode,iter)=selection.get_selected()
         if iter:
             name=mode.get(iter,0)[0]
             type=mode.get(iter,1)[0]
             size=mode.get(iter,2)[0]
             defualt=mode.get(iter,3)[0]
             constraint=mode.get(iter,5)[0]
             self.edit_id=mode.get(iter,6)[0]
             self.edit_field=iter
             column_name=self.wTree.get_widget("column_name")
             column_name.set_text(name)
             
             column_type=self.wTree.get_widget("column_type")
             column_type.set_active(self.find_index(dataTypes, type))
             
             column_size=self.wTree.get_widget("column_size")
             column_size.set_text(size)
             
             column_default=self.wTree.get_widget("column_default")
             column_default.set_text(defualt)

                
             con_array=constraint.split(",")
             column_primarykey=self.wTree.get_widget("column_primarykey")
             if self.find_index(con_array, 'PRIMARY KEY')!=-1 : column_primarykey.set_active(True)
             
             
            
             
             column_unique=self.wTree.get_widget("column_unique")
             if self.find_index(con_array, 'UNIQUE')!=-1 : column_unique.set_active(True)
             
             column_notnull=self.wTree.get_widget("column_notnull")         
             if self.find_index(con_array, 'NOT NULL')!=-1 : column_notnull.set_active(True)
             
             
             column_autoincrement=self.wTree.get_widget("column_autoincrement")
             if self.find_index(con_array, 'PRIMARY KEY')!=-1 and self.find_index(con_array, 'NOT NULL')!=-1 and type==dataTypes[0]:
                 column_autoincrement.set_active(True) 
             
    
     def check_columns(self,row): 
         """check rows for valid column"""
         iter=self.tbl_columns_rows.get_iter_first()
         while iter!=None :
             if row[6]!=self.tbl_columns_rows.get_value(iter,6):
                 if row[0]==self.tbl_columns_rows.get_value(iter,0):
                     return 107
                 if self.find_index(row[5].split(","),'PRIMARY KEY')!=-1 and self.find_index(row[5].split(","),'NOT NULL')!=-1 and row[1]==dataTypes[0] :
                     return 111
             iter=self.tbl_columns_rows.iter_next(iter)
         return 0
     
     def drop_table(self,widget):
         """drop table on click event"""
         selection=self.tables.get_selection()
         (mode,iter)=selection.get_selected()
         if iter:
             table=mode.get(iter,0)[0]
             if self.show_msg(108, "warning","yesno")==gtk.RESPONSE_YES:
                 self.cur.execute("DROP TABLE %s"%(table))
                 mode.remove(iter)
                 for col in self.db_table.get_columns() :
                     self.db_table.remove_column(col)                 
                 if self.tbl_rows!=None:
                     self.tbl_rows.clear()
                 self.set_table_sensitive(False)
         else  :
             self.show_msg(109,"info")
             return 
                 
     def rename_table(self,widget):
         """rename table on click event"""

         
         table=self.get_selected_table()
         if table !='':
             table_name_last=table
             table_name_new=None
             edit_table_name_window=gtk.Dialog("Rename table name",
                                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                             gtk.STOCK_OK, gtk.RESPONSE_OK)
                                )             
             edit_table_name_window.set_size_request(200, 70)

             
             hbox=gtk.HBox(False,5)
             
             lable=gtk.Label("Name: ")
             lable.show()
             hbox.pack_start(lable, False, False, 0)
             
             text=gtk.Entry()
             text.set_text(table_name_last)
             text.show()
             hbox.pack_start(text, True, True, 0)
             
             hbox.show()
             edit_table_name_window.vbox.pack_start(hbox, True, True, 0)
             
             if edit_table_name_window.run()==gtk.RESPONSE_OK:
                 if table_name_last==text.get_text().strip():
                     edit_table_name_window.destroy()
                 elif text.get_text().strip()=="":
                     self.show_msg(110)
                     edit_table_name_window.destroy()
                 else:
                     self.cur.execute("Select Name FROM sqlite_master WHERE type='table' and name='%s' ORDER BY Name"%(text.get_text().strip()))
                     rows=self.cur.fetchall()
                     if len(rows)!=0:
                         self.show_msg(114)
                         edit_table_name_window.destroy()
                         return 
                     self.cur.execute("ALTER TABLE %s RENAME TO %s "%(self.table_name_last,self.table_name_new.get_text()))
                     self.load_tables()
                     edit_table_name_window.destroy()                     
             else :
                 edit_table_name_window.destroy()

         else:
             self.show_msg(109,"info")
    
         
     def apply_changes(self,widget):
         """applay table changes"""
         table_name=self.wTree.get_widget("table_name")
         if table_name.get_text()=='':
             self.show_msg(110)
             table_name.grab_focus()
             return
         sql="CREATE TABLE %s ( "%(table_name.get_text()) 
         rows=self.get_column_rows()
         is_first=True
         for row in rows :
             name=row[0]
             type=row[1]
             size=row[2]
             if size.strip()!="":
                 size=" (%s) " % size
             value=row[3]
             constraint=row[4]
             if is_first==False:
                 sql+=" , "
             sql+=" %s %s %s %s %s "%(name , type,size,value,constraint)
             is_first=False
         
         sql+=" ) "
         print sql
         
         if self.cur==None:
             self.show_msg(113)
             
             return 
         try:
             self.cur.execute(sql)
             self.load_tables()
             self.hide_table_view("")
         except sqlite.DatabaseError , errormsg:
             ERRORS[112][1]=sql+'\n\n'+errormsg.__str__()
             self.show_msg(112)
         
         
     def get_column_rows(self):    
         """get all row of column rows"""
         rows=[]
         iter=self.tbl_columns_rows.get_iter_first()
         while iter!=None :
             row=[]
             row.append(self.tbl_columns_rows.get_value(iter,0))
             row.append(self.tbl_columns_rows.get_value(iter,1))
             row.append(self.tbl_columns_rows.get_value(iter,2))
             row.append(self.tbl_columns_rows.get_value(iter,3))
             row.append(self.tbl_columns_rows.get_value(iter,4))
             row.append(self.tbl_columns_rows.get_value(iter,5))
             row.append(self.tbl_columns_rows.get_value(iter,6))             
             rows.append(row)
             iter=self.tbl_columns_rows.iter_next(iter)
         return rows
         
     def get_selected_table(self):
         """get selected table"""
         selection=self.tables.get_selection()
         (mode,iter)=selection.get_selected()
         if iter:
             table=mode.get(iter,0)[0]
             return table
         else:
             return ""
     def execute_sql(self,widget,openagain=False): 
         """open window to execute sql comamnd """
         
         
         exe_win=gtk.Dialog("Enter SQL",
                            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OK, gtk.RESPONSE_OK)
                            )
         exe_win.set_size_request(400, 100)
         #exe_win.add_buttons(gtk.STOCK_OK,gtk.STOCK_CANCEL)

         label=gtk.Label()
         label.set_label("Enter SQL script :")
         exe_win.vbox.pack_start(label, True, True, 0)
         
         label.show()
         
         text=gtk.Entry()
         if openagain==True:
             text.set_text(widget)
         else:
             text.set_text(self.sql_history)
         exe_win.vbox.pack_start(text, True, True, 0)
         text.show()
         

         if exe_win.run()==gtk.RESPONSE_OK:
            try:                 
                 self.cur.execute(text.get_text())
                 self.con.commit()
                 rows=self.cur.fetchall()
                 self.sql_history=text.get_text()
                 if len(rows)!=0:
                     row_first=rows[0]
                     num_col=len(row_first)

                     #remove Last columns from db_table TreeView
                     for col in self.db_table.get_columns() :
                         self.db_table.remove_column(col)
                      
                     list=[]
                     for i in (self.cur.description):
                         list.append(gobject.TYPE_STRING)
    
                     t = tuple(list)
                     
                     self.tbl_rows = gtk.ListStore(*t)
                     cell = gtk.CellRendererText()
                     index=0
                     for fieldDesc in self.cur.description:
                         col = gtk.TreeViewColumn(fieldDesc[0],cell,text=index)
                         self.db_table.append_column(col)
                         self.db_table.get_column(index).set_resizable(True)
                         index+=1
                         
                         
                     self.db_table.set_model(self.tbl_rows)
                     
                     for rcd in rows:
                         self.tbl_rows.append(rcd)
                         
                     self.set_table_sensitive(True)                       
                 #self.cur.execute("insert into fred2 values ('F','hmmsmm','s3432tone','br243ead?')")
                 
                 exe_win.destroy()
            except sqlite.OperationalError, errormsg:
                ERRORS[112][1]=text.get_text()+'\n\n'+errormsg.__str__()
                self.show_msg(112)
                exe_win.destroy()
                self.execute_sql(text.get_text(), True)
            except sqlite.IntegrityError, errormsg:
                ERRORS[112][1]=text.get_text()+'\n\n'+errormsg.__str__()
                self.show_msg(112)
                exe_win.destroy()
                self.execute_sql(text.get_text(), True)
                
         else:
             exe_win.destroy()
         
         
            
              
     def about(self,widget):     
        about=gtk.AboutDialog()
        about.set_name("pySQLiteGUI")
        about.set_version(__version__)
        about.set_comments("It is a cross-platform, GTK2 GUI tool for creating and managing SQLite databases.")
        about.set_authors(["Milad Rastian <milad@rastian.com>"])
        about.set_artists(["GUI","    Mitchell Foral","    Milad Rastian <milad@rastian.com>"])
        about.set_license("pySQLiteGUI is free software; you can redistribute it and/or modify\nit under the terms of the GNU General Public License as published by\nthe Free Software Foundation; either version 2 of the License, or\n(at your option) any later version.")
        about.set_transient_for(self.main_window)
        about.set_website("http://pysqlitegui.osp.ir")         
        result=about.run()
        about.destroy()
if __name__ == '__main__':
    from sys import argv
    if argv[1:] and argv[1] in ('-h', '--help'):
        print argv[0] , "Help ..."
    elif len (argv)==1:
        pSqliteGUIActions()
        gtk.main()
         
