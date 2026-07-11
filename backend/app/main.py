import os
from fastapi import FastAPI,Depends,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import Base,engine,get_db,SessionLocal
from .models import *
from .security import hash_password,verify_password,create_token,current_user
app=FastAPI(title="REI'SPETOS OS API",version="1.0.0")
front=os.getenv("FRONTEND_URL","*")
app.add_middleware(CORSMiddleware,allow_origins=["*"] if front=="*" else [front],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
class LoginIn(BaseModel): username:str;password:str
class ProductIn(BaseModel): name:str;cost:float;price:float;stock:float;min_stock:float=10;sector:str="Bar"
class TableIn(BaseModel): name:str;customer_name:str=""
class ItemIn(BaseModel): product_id:int;qty:float;note:str=""
class CloseIn(BaseModel): payment_method:str
class StockIn(BaseModel): product_id:int;movement_type:str;qty:float;note:str=""
class CustomerIn(BaseModel): name:str;phone:str
class ReservationIn(BaseModel): customer_name:str;phone:str;date:str;time:str;people:int=2;table_name:str=""
class ExpenseIn(BaseModel): description:str;category:str="Outros";amount:float;status:str="pending"
def audit(db,u,a,d=""): db.add(AuditLog(username=u["username"],action=a,detail=d))
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine);db=SessionLocal()
    try:
        if not db.query(User).filter_by(username="admin").first(): db.add(User(username="admin",password_hash=hash_password("1234"),role="admin"))
        if not db.query(User).filter_by(username="caixa").first(): db.add(User(username="caixa",password_hash=hash_password("0000"),role="caixa"))
        if db.query(Product).count()==0: db.add_all([Product(name="Heineken",cost=6.19,price=12,stock=72,min_stock=20,sector="Bar"),Product(name="Brahma/Skol",cost=2.65,price=8,stock=80,min_stock=20,sector="Bar"),Product(name="Original",cost=3.3,price=7,stock=60,min_stock=20,sector="Bar"),Product(name="Espeto de Carne",cost=4.3,price=10,stock=100,min_stock=20,sector="Churrasqueira"),Product(name="Chopp 500ml",cost=3.8,price=10,stock=200,min_stock=30,sector="Bar"),Product(name="Batata Frita",cost=7,price=24,stock=30,min_stock=10,sector="Cozinha")])
        db.commit()
    finally: db.close()
@app.get("/health")
def health(): return {"ok":True,"system":"REI'SPETOS OS"}
@app.post("/auth/login")
def login(p:LoginIn,db:Session=Depends(get_db)):
    u=db.query(User).filter_by(username=p.username.lower().strip()).first()
    if not u or not verify_password(p.password,u.password_hash): raise HTTPException(401,"Usuário ou senha inválidos")
    return {"token":create_token(u.username,u.role),"username":u.username,"role":u.role}
@app.get("/dashboard")
def dashboard(u=Depends(current_user),db:Session=Depends(get_db)):
    r=float(db.query(func.coalesce(func.sum(Sale.total),0)).scalar() or 0);c=float(db.query(func.coalesce(func.sum(Sale.cost_total),0)).scalar() or 0);e=float(db.query(func.coalesce(func.sum(Expense.amount),0)).filter(Expense.status=="paid").scalar() or 0)
    return {"revenue":r,"cost":c,"expenses":e,"profit":r-c-e,"low_stock":db.query(Product).filter(Product.stock<=Product.min_stock).count(),"open_tables":db.query(TableOrder).filter(TableOrder.status=="open").count()}
@app.get("/products")
def products(u=Depends(current_user),db:Session=Depends(get_db)): return db.query(Product).filter(Product.active==True).order_by(Product.name).all()
@app.post("/products")
def add_product(p:ProductIn,u=Depends(current_user),db:Session=Depends(get_db)):
    if u["role"]!="admin": raise HTTPException(403,"Apenas administrador")
    x=Product(**p.model_dump());db.add(x);audit(db,u,"Produto criado",x.name);db.commit();db.refresh(x);return x
@app.get("/tables")
def tables(u=Depends(current_user),db:Session=Depends(get_db)):
    out=[]
    for t in db.query(TableOrder).filter(TableOrder.status=="open").order_by(TableOrder.name).all():
        items=db.query(OrderItem).filter(OrderItem.table_id==t.id).all();out.append({"id":t.id,"name":t.name,"customer_name":t.customer_name,"status":t.status,"total":sum(i.qty*i.unit_price for i in items),"items":items})
    return out
@app.post("/tables")
def open_table(p:TableIn,u=Depends(current_user),db:Session=Depends(get_db)):
    if db.query(TableOrder).filter(TableOrder.name==p.name,TableOrder.status=="open").first(): raise HTTPException(409,"Mesa já aberta")
    t=TableOrder(name=p.name,customer_name=p.customer_name,status="open");db.add(t);audit(db,u,"Mesa aberta",p.name);db.commit();db.refresh(t);return t
@app.post("/tables/{tid}/items")
def add_item(tid:int,p:ItemIn,u=Depends(current_user),db:Session=Depends(get_db)):
    t=db.get(TableOrder,tid);pr=db.get(Product,p.product_id)
    if not t or t.status!="open": raise HTTPException(404,"Mesa não encontrada")
    if not pr: raise HTTPException(404,"Produto não encontrado")
    if pr.stock<p.qty: raise HTTPException(400,"Estoque insuficiente")
    pr.stock-=p.qty;i=OrderItem(table_id=t.id,product_id=pr.id,product_name=pr.name,qty=p.qty,unit_price=pr.price,unit_cost=pr.cost,sector=pr.sector,note=p.note,status="waiting");db.add(i);db.add(StockMovement(product_id=pr.id,product_name=pr.name,movement_type="sale",qty=-p.qty,note=t.name));audit(db,u,"Item lançado",f"{t.name} - {p.qty}x {pr.name}");db.commit();db.refresh(i);return i
@app.post("/tables/{tid}/close")
def close_table(tid:int,p:CloseIn,u=Depends(current_user),db:Session=Depends(get_db)):
    t=db.get(TableOrder,tid)
    if not t or t.status!="open": raise HTTPException(404,"Mesa não encontrada")
    items=db.query(OrderItem).filter(OrderItem.table_id==tid).all();total=sum(i.qty*i.unit_price for i in items);cost=sum(i.qty*i.unit_cost for i in items);db.add(Sale(origin="table",reference=t.name,total=total,cost_total=cost,payment_method=p.payment_method));t.status="closed";audit(db,u,"Mesa fechada",f"{t.name} - {total:.2f}");db.commit();return {"ok":True,"total":total}
@app.get("/production")
def production(u=Depends(current_user),db:Session=Depends(get_db)): return db.query(OrderItem).filter(OrderItem.status!="delivered").order_by(OrderItem.id.desc()).all()
@app.post("/production/{iid}/{status}")
def prod_status(iid:int,status:str,u=Depends(current_user),db:Session=Depends(get_db)):
    i=db.get(OrderItem,iid)
    if not i: raise HTTPException(404,"Pedido não encontrado")
    if status not in ["waiting","preparing","ready","delivered"]: raise HTTPException(400,"Status inválido")
    i.status=status;audit(db,u,"Status de produção",f"{i.product_name} - {status}");db.commit();return {"ok":True}
@app.get("/customers")
def customers(u=Depends(current_user),db:Session=Depends(get_db)): return db.query(Customer).order_by(Customer.name).all()
@app.post("/customers")
def add_customer(p:CustomerIn,u=Depends(current_user),db:Session=Depends(get_db)):
    if db.query(Customer).filter_by(phone=p.phone).first(): raise HTTPException(409,"Telefone já cadastrado")
    c=Customer(name=p.name,phone=p.phone);db.add(c);audit(db,u,"Cliente cadastrado",p.name);db.commit();db.refresh(c);return c
@app.get("/reservations")
def reservations(u=Depends(current_user),db:Session=Depends(get_db)): return db.query(Reservation).order_by(Reservation.id.desc()).all()
@app.post("/reservations")
def add_reservation(p:ReservationIn,u=Depends(current_user),db:Session=Depends(get_db)):
    r=Reservation(**p.model_dump());db.add(r);audit(db,u,"Reserva criada",f"{r.customer_name} {r.date} {r.time}");db.commit();db.refresh(r);return r
@app.get("/expenses")
def expenses(u=Depends(current_user),db:Session=Depends(get_db)):
    if u["role"]!="admin": raise HTTPException(403,"Apenas administrador")
    return db.query(Expense).order_by(Expense.id.desc()).all()
@app.post("/expenses")
def add_expense(p:ExpenseIn,u=Depends(current_user),db:Session=Depends(get_db)):
    if u["role"]!="admin": raise HTTPException(403,"Apenas administrador")
    e=Expense(**p.model_dump());db.add(e);audit(db,u,"Despesa criada",p.description);db.commit();db.refresh(e);return e
@app.get("/audit")
def logs(u=Depends(current_user),db:Session=Depends(get_db)):
    if u["role"]!="admin": raise HTTPException(403,"Apenas administrador")
    return db.query(AuditLog).order_by(AuditLog.id.desc()).limit(200).all()
