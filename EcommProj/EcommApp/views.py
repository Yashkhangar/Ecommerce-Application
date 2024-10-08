from django.shortcuts import render,HttpResponse,redirect
from . models import Product,CartItem,Order
from .forms import CreateUserForm,AddProduct
from django.contrib import messages
from django.contrib.auth import login,logout,authenticate
import random
import razorpay
from django.contrib.auth.decorators import user_passes_test

# Create your views here.
def index(req):
    products = Product.objects.all()
    context ={}
    context['products'] = products
    return render(req,"index.html",context)

def prodDetails(req,pid):
    products = Product.objects.get(product_id = pid)
    context ={}
    context['products'] = products
    return render(req,"productDetail.html",context)

def viewCart(req):
    if req.user.is_authenticated:
        cart_item = CartItem.objects.filter(user = req.user)
    else:
        cart_item = CartItem.objects.filter(user = None)
        messages.warning(req,"Log in to add to cart")
    context ={}
    context['items'] = cart_item
    total_price = 0
    for x in cart_item:
        #print(x.product.price,x.quantity)
        total_price += (x.product.price * x.quantity)
        #print(total_price)
    context['total'] = total_price
    length = len(cart_item)
    context["length"] = length
    return render(req,"cart.html",context)

def addCart(req,pid):
    prodcuts = Product.objects.get(product_id = pid)
    user = req.user if req.user.is_authenticated else None
    if user:
        cart_item,created = CartItem.objects.get_or_create(product = prodcuts,user =user)
    else:
        return redirect("/login")
    print(cart_item,created)
    if not created:
        cart_item.quantity += 1
    else:
        cart_item.quantity = 1
    cart_item.save()
    return redirect("/viewCart")

def removeCart(req,pid):
    products = Product.objects.get(product_id = pid)
    cart_item = CartItem.objects.filter(product=products,user = req.user)
    cart_item.delete()
    return redirect("/viewCart")

#1. get the values from the form
#2.  apply the price range function from the custom manager
def range(req):
    if req.method == "GET" :
        return redirect("/")
    else:
        min = req.POST["min"]
        max = req.POST["max"]
        #Using Custom Manager
        if min != "" and max !="" and min is not None and max is not None:
            queryset = Product.prod.get_price_range(min,max)
            #using Default Manager
            #queryset = Product.objects.filter(price__range = (min,max))
            context ={}
            context['products'] = queryset
            return render(req,"index.html",context)
        else:
            return redirect("/")
    
def watchList(req):
    if req.method == "GET" :
        queryset = Product.prod.watch_list()
        #using Default Manager
        #queryset = Product.objects.filter(price__range = (min,max))
        context ={}
        context['products'] = queryset
        return render(req,"index.html",context)
    
def mobileList(req):
    if req.method == "GET" :
        queryset = Product.prod.mobile_list()
        #using Default Manager
        #queryset = Product.objects.filter(price__range = (min,max))
        context ={}
        context['products'] = queryset
        return render(req,"index.html",context)
    
def priceOrder(req):
    queryset = Product.objects.all().order_by('price')
    context ={}
    context['products'] = queryset
    return render(req,"index.html",context)

def descpriceOrder(req):
    queryset = Product.objects.all().order_by('-price')
    context ={}
    context['products'] = queryset
    return render(req,"index.html",context)

def updateqty(req,uval,pid):
    products = Product.objects.get(product_id = pid)
    a = CartItem.objects.filter(product= products)
    print(a)
    print(a[0])
    print(a[0].quantity)
    if uval == 1:
        temp = a[0].quantity + 1
        a.update(quantity = temp)
    else:
        temp = a[0].quantity-1
        a.update(quantity = temp)
    return redirect("viewCart")

def viewOrder(req):
    cart_item = CartItem.objects.filter(user = req.user)
    print(cart_item)
    """ oid = random.randrange(1000,9999)
    for x in cart_item:
        Order.objects.create(order_id = oid,product_id = x.product.product_id,quantity = x.quantity, user=req.user)
        #x.delete()
    orders = Order.objects.filter(user=req.user,is_completed = False) """
    context ={}
    context['items'] = cart_item
    total_price = 0
    for x in cart_item:
        #print(x.product.price,x.quantity)
        total_price += (x.product.price * x.quantity)
        #print(total_price)
    context['total'] = total_price
    length = len(cart_item)
    context["length"] = length
    return render(req, "viewOrder.html",context)

def register_user(req):
    form = CreateUserForm()
    if req.method == "POST":
        form = CreateUserForm(req.POST)
        if form.is_valid():
            form.save()
            messages.success(req,"User Created Successfully")
            return redirect("/")
        else:
            messages.error(req,"Incorrect Username or Password Format")
    context = {'form':form}
    return render(req,"register.html",context)

def login_user(req):
    if req.method == "POST":
        username = req.POST['username']
        password = req.POST['password']
        user = authenticate(req,username=username,password=password)
        if user is not None:
            login(req,user)
            messages.success(req,("Logged in Successfully"))
            return redirect("/")
        else:
            messages.error(req,("There was an error. Try Again!!!"))
            return redirect("/login")
    else:
        return render(req,"login.html")  


def logout_user(req):
    logout(req)
    messages.success(req,("Logged Out Successfully"))
    return redirect('/')

def makePayment(req):
    c = CartItem.objects.filter(user = req.user)
    oid = random.randrange(1000,9999)
    for x in c:
        Order.objects.create(order_id = oid,product_id = x.product.product_id,quantity = x.quantity, user=req.user)
        #x.delete()
    orders = Order.objects.filter(user = req.user,is_completed = False)
    total_price = 0
    for x in orders:
        total_price += (x.product.price * x.quantity)
        oid = x.order_id
    client = razorpay.Client(auth=("rzp_test_eEEzc0d8GHJgYL", "ZI7HtSUusg8kp6xU4DlFkHo5"))
    data = {"amount": total_price * 100,
            "currency": "INR",
            "receipt": oid}
    payment = client.order.create(data = data)
    context = {}
    context['data'] = payment
    context['amount'] = payment["amount"]
    # Once payment is done, cart should get empty
    c.delete()
    orders.update(is_completed = True)
    return render(req,"payment.html",context)

def myOrders(req):
    orders = Order.objects.filter(user = req.user)
    context ={}
    context['items'] = orders
    return render(req,"myOrder.html",context)

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def insertProduct(req):
    if req.user.is_authenticated:
        user =  req.user
        if req.method =="GET":
            form = AddProduct()
            return render(req,"insertProd.html",{'form':form,"username":user})
        else:
            form = AddProduct(req.POST,req.FILES or None)
            if form.is_valid():
                form.save()
                return redirect("/")
            else:
                return render(req,"insertProd.html",{'form':form,"username":user})
    else:
        return redirect("/login")