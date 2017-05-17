"""
MD Novel Tools

tree view
    http://www.tkdocs.com/tutorial/tree.html
    https://docs.python.org/3/library/tkinter.ttk.html#tkinter.ttk.Treeview
    https://docs.python.org/3/library/tkinter.html
    http://www.tkdocs.com/tutorial/styles.html

-Double spaces in a target file
insert at position
-build
    -build with metadata file
File Status in Tree
File Tags
reorder file
rename file
-open file
add new file
Preview file contents, tooltip or column
-count words
-get metadata
remember toggle states
remember window size
remember column states
custom metadata for each file
    project file stored above MS
Treeview file icons
    http://stackoverflow.com/questions/9203251/how-can-i-get-an-icon-or-thumbnail-for-a-specific-file
Replacements List


"""
import tkinter
from tkinter import ttk
from tkinter import filedialog
import os
import re
import pypandoc
from subprocess import call
from datetime import datetime
import yaml
import locale

class App:
    def __init__(self):
        locale.setlocale(locale.LC_ALL, '')

        # class instance variables
        self.metadata = ''
        self.startpath = ''
        self.projecttile = ''
        self.projectsubtitle = ''
        self.authors = []
        self.alwaysUp = False
        self.showDate = False
        # Get Last Dir
        self.startpath = self.RetreiveLastPath()
        print(self.startpath)
        # Start GUI
        self.top = tkinter.Tk()
        """
        ttk.Style().configure(style='TButton', background="#333", foreground='#ddd')
        ttk.Style().configure(style='TLabel', background="#333", foreground='#ddd')
        ttk.Style().configure(style='Treeview', background="#333", foreground='#ddd')
        """
        self.top.minsize(width=200, height=200)
        self.top.geometry('300x500')
        self.tree = ttk.Treeview(self.top, columns=('words', 'modified', 'note'))
        self.SetWindowTitle()
        # Headings
        self.tree.heading('#0', text='Files')
        self.tree.heading('words', text='Words')
        self.tree.heading('modified', text='Date')
        self.tree.heading('note', text='Note')
        # Columns
        self.tree.column('#0', width=150, minwidth=50, stretch=False)
        self.tree.column('words', anchor='e', width=50, minwidth=20, stretch=False)
        self.tree.column('modified', anchor='e', width=150, minwidth=50, stretch=False)
        self.tree.column('note', minwidth=100)
        self.tree.tag_configure('md', foreground='blue')
        self.tree.tag_bind('md', '<Double-1>', self.ItemClicked)
        
        # try to fill the tree
        self.GetFileTree ()
        # Scroll bar for treeview
        self.treescroll = tkinter.Scrollbar(self.tree)
        self.treescroll.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=self.treescroll.set)
        self.treescroll.configure(command=self.tree.yview)

        self.treescrollx = tkinter.Scrollbar(self.tree)
        self.treescrollx.pack(side='bottom', fill='x')
        self.tree.configure(xscrollcommand=self.treescrollx.set)
        self.treescrollx.configure(command=self.tree.xview, orient=tkinter.HORIZONTAL)

        self.tree.pack(fill='both', expand=1)
        # Add toolbar
        self.AddTools()
        self.top.title('MD Novel Tools')
        self.top.mainloop()

    def ClearTree (self):
        self.tree.delete()

    def GetFileTree (self):
        # check path
        if self.startpath is '':
            return
        self.GetMetadata()
        self.tree.delete(*self.tree.get_children())
        #print(startpath)
        for root, dirs, files in os.walk(self.startpath):
            level = root.replace(self.startpath, '').count(os.sep)
            p = os.path.dirname(root)
            d = root
            n = os.path.basename(d)
            # our root-level item should be attached to the blank parent
            if level is 0:
                p = ''
            self.tree.insert(p, 'end', d, text=n)
            indent = ' ' * 4 * (level)
            #print('{}{}/'.format(indent, os.path.basename(root)))
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                x = d + os.sep + f
                self.tree.insert(d, 'end', x, text=f)
                #print('{}{}'.format(subindent, f))
                self.tree.item(x, tags=('md'))
            self.tree.item(d, open=True)
            self.tree.item(d, tags=('folder'))
        self.GetFolderSizes(self.startpath)

    def GetFolderSizes(self, p):
        #go through the tree and calculate folder sizes.
        words = self.GetFileWords(p)
        #recurse
        children = self.tree.get_children(p)
        for each in children:
            words += self.GetFolderSizes(each)
        #reformat
        n = locale.format('%d', words, grouping=True)
        #apply
        self.tree.set(p, 'words', n)
        return words
        
    def GetFileWords(self, f):
        #check if the item is a file
        count = 0
        if os.path.exists(f) and os.path.isfile(f):
            #
            with open(f, 'r', encoding='utf8') as t:
                text = t.read()
                count = len(text.split())
                self.GetFirstCommentText(text, f)
                date = os.path.getmtime(f)
                date = datetime.fromtimestamp(date)
                date = date.strftime('%m/%d/%Y %I:%M %p')
                self.tree.set(f, 'modified', date)
        return count

    def ItemClicked (self, event):
        item = self.tree.selection()[0]
        print(item)
        if os.path.isfile(item):
            os.startfile(item)
    

    """
    Actual Tool Scripts

    Define scripts above, and make sure to add buttons and pack them.
    """

    def DoubleSpace (self):
        search = r"(?<!\n)(\n)(?!\n)"
        replacement = "\n\n"
        for item in self.tree.selection():
            with open(item, 'r+', encoding='utf8') as i:
                c = i.read()
                c = re.sub(search, replacement, c)
                i.seek(0)
                i.write(c)
                i.truncate()

    def CompileManuscript(self):
        # first pack it all up
        ms = ''
        for root, dirs, files in os.walk(self.startpath):
            d = os.path.realpath(root)
            for f in files:
                p = d + os.sep + f
                with open(p, 'r', encoding='utf8') as fo:
                    ms += fo.read()
        with open('ms.md', 'w', encoding='utf8') as md:
            md.write(ms)
        # now compile it to formats
        self.CompileStripped('ms.md', 'html')
        print('\a')

    def CompileStripped(self, doc, targetformat):
        #doc = self.tree.selection()[0]
        content = ''
        with open(doc, 'r', encoding='utf8') as d:
            content = d.read();
        content = self.StripComments(content)
        output = pypandoc.convert(content,
            format='markdown',
            to=targetformat,
            extra_args=['-s'])
        targetpath = 'ms.' + targetformat
        with open(targetpath, 'w', encoding='utf8') as oo:
            oo.write(output)

    def PickStartDir(self):
        t = 'Pick the root level directory of your manuscript'
        path = filedialog.askdirectory(title=t)
        print(path)
        self.startpath = path
        self.StoreLastPath(self.startpath)
        self.GetFileTree()
    
    def ToggleStayUp(self):
        self.alwaysUp = not self.alwaysUp
        if self.alwaysUp:
            self.top.wm_attributes("-topmost", 1)
            self.b_au.state(['pressed'])
        else:
            self.top.wm_attributes("-topmost", 0)
            self.b_au.state(['!pressed'])

    def ToggleDate(self):
        self.showDate = not self.showDate
        if self.showDate:
            self.tree.configure(displaycolumns='words note')
            self.b_td.state(['pressed'])
        else:
            self.tree.configure(displaycolumns='words modified note')
            self.b_td.state(['!pressed'])

    def MetadataFile(self):
        metadatafilename = 'metadata.yaml'
        metadatapath = self.startpath + os.sep + metadatafilename
        initialcontents = """---
title: 'A Tale of Three Cities'
author: 'Ernest Shakespear'
editor: 'B. Precise'
publisher: 'Thor Books'
tags: [fiction, novel, literature]
...

        """
        if not os.path.exists(metadatapath):
            with open(metadatapath, 'w', encoding='utf8') as mdfo:
                mdfo.write(initialcontents)
        os.startfile(metadatapath)



    def AddTools(self):
        # Spacing
        #self.l_buttons = ttk.Label(self.top, text='Tools')
        #self.l_buttons.pack(side='top', fill='x')
        #self.l_es = ttk.Label(self.top, text=' ')
        #self.l_es.pack(side='bottom', fill='x')
        # Buttons
        self.tools = tkinter.Frame()
        self.tools.pack(padx=10, pady=10)
        ttk.Button (self.tools,
            text = "Pick Dir",
            command = self.PickStartDir).grid(row=0,column=0)
        ttk.Button (self.tools,
            text = "Rebuild Tree",
            command = self.GetFileTree).grid(row=1,column=0)
        ttk.Button (self.tools,
            text = "Unify Newlines",
            command = self.DoubleSpace).grid(row=0,column=1)
        ttk.Button (self.tools,
            text = "Compile MS",
            command = self.CompileManuscript).grid(row=2,column=0)
        self.b_au = ttk.Button(self.tools,
            text = 'Always on Top',
            command = self.ToggleStayUp)
        self.b_au.grid(row=0,column=2)
        self.b_td = ttk.Button(self.tools,
            text = 'Toggle Date',
            command = self.ToggleDate)
        self.b_td.grid(row=1,column=2)
        ttk.Button (self.tools,
            text = "Metadata",
            command = self.MetadataFile).grid(row=1,column=1)
        # Pack it all
        #self.ToolbarPacker()
    """ 
    def ToolbarPacker(self):
        for tool in self.buttons:
            #tool.pack(side='left', expand=1, fill='both')
            tool.pack(fill='both')
    """

    """
    Utilities
    """

    def StripComments(self, raw):
        lines = raw.split('\n')
        output = []
        for l in lines:
            if l.startswith('>') and l.endswith('<'):
                output.append('')
            else:
                output.append(l)
        return '\n'.join(output)

    def GetFirstCommentFile(self, path):
        with open(path, 'r', encoding='utf8') as fo:
            GetFirstCommentText(fo.read())
            
    def GetFirstCommentText(self, text, path):
        c = ''
        lines = text.split('\n')
        for l in lines:
            if l.startswith('>') and l.endswith('<'):
                c += l
                self.tree.set(path, 'note', c)
                return
    
    def GetMetadata(self):
        metadatafilename = 'metadata.yaml'
        metadatapath = self.startpath + os.sep + metadatafilename
        if os.path.exists(metadatapath):
            with open(metadatapath, 'r') as metaobject:
                self.metadata = yaml.load(metaobject.read())
                print(self.metadata)
            self.title = self.metadata['title']
            self.SetWindowTitle()

    def SetWindowTitle(self):
        if hasattr(self, 'top') and hasattr(self, 'title'):
            self.top.title("MD Novel Tools: " + self.title)

    def StoreLastPath(self, path):
        with open('lastpath.ini', 'w', encoding='utf8') as lpo:
            lpo.write(path)

    def RetreiveLastPath(self):
        if os.path.isfile('lastpath.ini'):
            with open('lastpath.ini', 'r', encoding='utf8') as lpo:
                lp = lpo.read()
                print(lp)
                return lp
        else:
            print('No lastpath.ini')
            return ''

if __name__ == "__main__":
    app = App()