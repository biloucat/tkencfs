#!/usr/bin/python3
req_version=(3,6)
import sys
assert(sys.version_info[:2] >= req_version)
import os
import subprocess
import shlex
import tkinter as tk
import tkinter.messagebox as messagebox
import tkinter.simpledialog as simpledialog
import tkinter.font as tkFont
import tkinter.ttk as ttk
      
class MultiColumnListbox(ttk.Frame):
  """use a ttk.TreeView as a multicolumn ListBox"""
  nblines=5
  def __init__(self,parent,headers,crypts,onSelect):
    super().__init__(parent)
    self._setup_widgets(headers,onSelect)
    self._build_tree(headers,crypts)

  def _setup_widgets(self,headers,onSelect):
    # create a treeview with dual scrollbars
    self.tree = ttk.Treeview(columns=headers, show="headings")
    vsb = ttk.Scrollbar(orient="vertical", command=self.tree.yview)
    hsb = ttk.Scrollbar(orient="horizontal", command=self.tree.xview)
    self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    self.tree.grid(column=0, row=0, sticky='nsew', in_=self)
    self.tree.bind("<<TreeviewSelect>>",onSelect)
    vsb.grid(column=1, row=0, sticky='ns', in_=self)
    hsb.grid(column=0, row=1, sticky='ew', in_=self)
    self.grid_columnconfigure(0, weight=1)
    self.grid_rowconfigure(0, weight=1)
  def _build_tree(self,headers,crypts):
    for col in headers:
      self.tree.heading(col, text=col.capitalize())
      # adjust the column's width to the header string
      self.tree.column(col, width=tkFont.Font().measure(col.capitalize()), anchor=tk.CENTER,stretch=False)

    for item in crypts:
      self.tree.insert('', 'end', values=item)
      # adjust column's width if necessary to fit each value
      for ix, val in enumerate(item):
        col_w = tkFont.Font().measure(val)
        if self.tree.column(ix,width=None)<col_w:
          self.tree.column(ix, width=col_w)
    self.tree.configure(height=self.nblines, selectmode=tk.BROWSE)
class ToolBar(tk.Frame):
  def __init__(self,parent,seqbuttons):
    super().__init__(parent)
    self.buttons={}
    for (text,state,command) in seqbuttons:
      b=tk.Button(self, text=text, state=state, width=10, command=command)
      b.pack(side=tk.LEFT, padx=2, pady=2)
      self.buttons[text]=b
class Application(tk.Frame):
  #https://en.wikipedia.org/wiki/Filename
  badcharacters=' \'/"'
  @staticmethod
  def selectMark(directory):
    with open('/etc/mtab') as mtabfile: # now read the file containing persistent data or being empty
      for line in mtabfile: 
        if line[:5]=="encfs":
          fields=line.split()
          if fields[1]==directory:
            return 'X'
    return ''
  
  def __init__(self, parent):
    #Create frame to contain all others
    super().__init__(parent)
    parent.option_add("*Dialog.msg.wrapLength", "15cm")
    parent.title('Gui for EncFs')
    self.lock=False
    parent.protocol("WM_DELETE_WINDOW", self.onClose)
    self.userpath=os.path.join(os.path.expanduser("~") ,'.tkencfs')
    pathtofiles=os.path.join(self.userpath,'Encrypted_dirs')
    os.makedirs(pathtofiles,mode=0o755,exist_ok=True)
    os.makedirs(os.path.join(self.userpath,'Mounted_dirs'),mode=0o755,exist_ok=True)
    self.labelpath=tk.Label(parent, text='Chemins vers les répertoires cryptés et montés',font=tkFont.Font(weight='bold'))
    self.labelpath.pack()
    crypts=[]
    with os.scandir(pathtofiles) as it:
      for entry in it:
        if entry.is_dir(follow_symlinks=False):
          try:
            mount=self.mountDir(entry.name)
          except RuntimeError as err:
            messagebox.showerror(f"scan de {pathtofiles}",err.args[0])
          else:
            l=[os.path.join(pathtofiles,entry.name),mount]
            l.append(self.selectMark(mount))
            crypts.append(l)
    self.multilistbox = MultiColumnListbox(parent,("répertoire crypté","répertoire à monter","monté"),crypts,self.onSelect)
    self.multilistbox.pack()
    self.toolbar=ToolBar(parent,(("Ajouter",tk.NORMAL,self.onAdd),("Enlever",tk.DISABLED,self.onDelete),("Monter",tk.DISABLED,self.encfsmount),("Démonter",tk.DISABLED,self.encfsumount)))
    self.toolbar.pack(side=tk.BOTTOM)
    #http://stackoverflow.com/questions/10448882/how-do-i-set-a-minimum-window-size-in-tkinter
    #minsize empêche width de grandir si ajout de grands noms dans multilistbox !!!
    #http://stackoverflow.com/questions/21958534/setting-the-window-to-a-fixed-size-with-tkinter
    parent.update()
    parent.minsize(parent.winfo_width(), parent.winfo_height())
    parent.maxsize(parent.winfo_width(), parent.winfo_height())
  def mountDir(self,cryptedDir,strict=False):
    basename=os.path.basename(cryptedDir)
    result=os.path.join(self.userpath,'Mounted_dirs',os.path.basename(cryptedDir))
    if strict and os.access(result, os.F_OK):
      raise RuntimeError(f"{result} must not exist")
    else:
      return result

  def onClose(self):
    if not self.lock:
      self.master.destroy()
  def onSelect(self,event):
    dirs=self.multilistbox.tree.item(self.multilistbox.tree.selection()[0],'values')
    if dirs[2]=='X':
      self.toolbar.buttons["Démonter"].configure(state=tk.NORMAL)
      self.toolbar.buttons["Monter"].configure(state=tk.DISABLED)
      self.toolbar.buttons["Enlever"].configure(state=tk.DISABLED)
    else:
      self.toolbar.buttons["Démonter"].configure(state=tk.DISABLED)
      self.toolbar.buttons["Monter"].configure(state=tk.NORMAL)
      if not os.access(dirs[0], os.F_OK) or os.listdir(dirs[0])==[]:
        self.toolbar.buttons["Enlever"].configure(state=tk.NORMAL)
      else:
        self.toolbar.buttons["Enlever"].configure(state=tk.DISABLED)
  def encfsmount(self):
    dirs=self.multilistbox.tree.item(self.multilistbox.tree.selection()[0],'values')
    try:
      os.mkdir(self.mountDir(dirs[0],strict=True),mode=0o700)
    except RuntimeError as err:
      messagebox.showerror("mount",err.args[0])
      return
    if not os.access(dirs[0], os.F_OK):  # check if crypted directory  exist
      os.mkdir(dirs[0],0o755)               # if not create the directory
      mkdir=True
    else:
      mkdir=False
    password=simpledialog.askstring("Password","Password",parent=self.master,show='*')  
    cmd =f"encfs --standard -S {dirs[0]} {dirs[1]}"# call encfs without prompting for password
    args=shlex.split(cmd)
    proc = subprocess.Popen(args,  
                         stdin=subprocess.PIPE, 
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         encoding='utf-8',
                        ) # open new process
    stdout_value, stderr_value = proc.communicate(password) # communicate is a one time action, afterwards proc is closed
    if (proc.returncode==0):
      dirs=dirs[:-1]+('X',)
      self.multilistbox.tree.item(self.multilistbox.tree.selection()[0],values=dirs)
      if stdout_value:
        messagebox.showinfo("mount",stdout_value)
      else: 
        messagebox.showinfo("mount",f"{dirs[1]} successfully mounted")
      self.toolbar.buttons["Démonter"].configure(state=tk.NORMAL)
      self.toolbar.buttons["Monter"].configure(state=tk.DISABLED)
      self.toolbar.buttons["Enlever"].configure(state=tk.DISABLED)
      #open mounted directory
      subprocess.run(["xdg-open",dirs[1]])# subprocess automaticaly closed
    else:
      os.rmdir(dirs[1])
      if mkdir:
        os.rmdir(dirs[0])
      messagebox.showerror("mount",f"returncode:{proc.returncode}\nstdout:{stdout_value}\nstderr:{stderr_value}")

  def encfsumount(self):
    dirs=self.multilistbox.tree.item(self.multilistbox.tree.selection()[0],'values')
    cmd =f"fusermount -u {dirs[1]}"
    args=shlex.split(cmd)
    completproc = subprocess.run(args, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 encoding='utf-8' #pierre ajouté
                        ) # automaticaly closed
    if (completproc.returncode==0):
      os.rmdir(dirs[1])
      dirs=dirs[:-1]+('',)
      self.multilistbox.tree.item(self.multilistbox.tree.selection()[0],values=dirs)
      messagebox.showinfo("umount",f"{dirs[1]} successfully umounted")
      self.toolbar.buttons["Démonter"].configure(state=tk.DISABLED)
      self.toolbar.buttons["Monter"].configure(state=tk.NORMAL)
      self.toolbar.buttons["Enlever"].configure(state=tk.DISABLED)
    else:  
      messagebox.showerror("umount",f"returncode:{completproc.returncode}\nstdout:{completproc.stdout}\nstderr:{completproc.stderr}")
  def onAdd(self):
    self.lock=True
    newcrypt=simpledialog.askstring("Nouveau répertoire","Répertoire crypté:",parent=self.master)
    self.lock=False
    if newcrypt:
      try:
        for c in self.badcharacters:
          if c in newcrypt:
            raise RuntimeError(f"\"{newcrypt}\" must not contain characters in '{self.badcharacters}'")
      except RuntimeError as err:
        messagebox.showerror("Add crypted directory",err.args[0])
        return
      newpath=os.path.join(self.userpath,'Encrypted_dirs',newcrypt)
      try:
        mountdir=self.mountDir(newpath,strict=True)
      except RuntimeError as err:
        messagebox.showerror("Add crypted directory",err.args[0])
        return
      crypts=[self.multilistbox.tree.item(item,'values')[0] for item in self.multilistbox.tree.get_children()]
      if newpath in crypts:
        messagebox.showerror("Add crypted directory",f"{newpath} already in the list")
        return
      item=[newpath,mountdir,'']
      itemid=self.multilistbox.tree.insert('', 'end', values=item)
      # adjust column's width if necessary to fit each value
      for ix, val in enumerate(item):
        col_w = tkFont.Font().measure(val)
        if self.multilistbox.tree.column(ix,width=None)<col_w:
          self.multilistbox.tree.column(ix, width=col_w)
      self.multilistbox.tree.see(itemid)
  def onDelete(self):
    dirs=self.multilistbox.tree.item(self.multilistbox.tree.selection()[0],'values')
    if os.access(dirs[0], os.F_OK):
      try:
        os.rmdir(dirs[0])
      except Exception as e:
        messagebox.showerror("delete directory",e)
        return
    self.multilistbox.tree.delete(self.multilistbox.tree.selection())
    #no selection anymore
    self.toolbar.buttons["Enlever"].configure(state=tk.DISABLED) 
    self.toolbar.buttons["Monter"].configure(state=tk.DISABLED)
## Main program
if __name__ == "__main__":
  Application(tk.Tk())
  tk.mainloop() 


