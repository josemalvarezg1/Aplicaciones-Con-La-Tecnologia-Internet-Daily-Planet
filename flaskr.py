from flask import Flask, render_template, request, session, json
from pymongo import *
from werkzeug import secure_filename
from bson import BSON
from bson import json_util
from bson.objectid import ObjectId
import time
import os
 
app = Flask(__name__, template_folder = 'templates', static_folder = 'static')
app.secret_key = 'F12Zr47j\3yX R~X@H!jmM]Lwf/,?KT'
app.config['UPLOAD_FOLDER'] = 'static/imagenes/'
# MongoDB Connection with PyMongo
client = MongoClient()

db = client.dailyplanet
users = db.users
comments = db.comments
posts = db.posts
username = ""
# Routes Definition
#Validar que exista una SESSION

@app.route('/')
def index():
	fechaPublic = time.strftime("%d/%m/%Y")
	todaysPosts = list(posts.find({"fecha": fechaPublic, "publicado": 1}))
	return render_template('articulosDeHoyNoSesion.html', todaysPosts = json.dumps(todaysPosts, default=json_util.default))

@app.route('/inicio')
def indexSesion():
	allPosts = list(posts.find({"publicado": 1}))
	username = session['name']
	user = users.find_one({ "correo": username })
	isReader = "false"
	if user["tipo"] == "Lector":
		isReader = "true"
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('articulosDeHoy.html', isAuthor = isAuthor, isReader = isReader, allPosts = json.dumps(allPosts, default=json_util.default))

@app.route('/login', methods=['POST'])
def login():
	username = request.form['email']
	password  = request.form['pass']
	user = users.find_one({ "correo": username })
	fechaPublic = time.strftime("%d/%m/%Y")
	todaysPosts = list(posts.find({"fecha": fechaPublic, "publicado": 1}))
	allPosts = list(posts.find({"publicado": 1}))
	if (user is None) or (len(user) == 0):
		return render_template('articulosDeHoyNoSesion.html', error = "true", todaysPosts = json.dumps(todaysPosts, default=json_util.default))
	if user["pass"] == password:
		session['name'] = username
		user = users.find_one({ "correo": username })
		isReader = "false"
		if user["tipo"] == "Lector":
			isReader = "true"
		isAuthor = "false"
		if user["tipo"] == "Autor":
			isAuthor = "true"
		return render_template('articulosDeHoy.html', user = username, isAuthor = isAuthor, isReader = isReader, allPosts = json.dumps(allPosts, default=json_util.default))
	return render_template('articulosDeHoyNoSesion.html', error = "true", todaysPosts = json.dumps(todaysPosts, default=json_util.default))

@app.route('/logout')
def indexNoSesion():
	session.pop('name', None)
	fechaPublic = time.strftime("%d/%m/%Y")
	todaysPosts = list(posts.find({"fecha": fechaPublic, "publicado": 1}))
	return render_template('articulosDeHoyNoSesion.html', todaysPosts = json.dumps(todaysPosts, default=json_util.default))

@app.route('/create')
def create():
	username = session['name']
	user = users.find_one({ "correo": username })
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('crearArticulo.html', user = session['name'], isAuthor = isAuthor)

@app.route('/draft')
def draft():
	username = session['name']
	user = users.find_one({ "correo": username })
	nombre = user["nombre"]
	apellido = user["apellido"]
	nombreCompleto = nombre+" "+apellido
	draftPosts = list(posts.find({"publicado": 0}))
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('articulosPorPublicar.html', user = session['name'], isAuthor = isAuthor, draftPosts = json.dumps(draftPosts, default=json_util.default))

@app.route('/publish')
def publish():
	username = session['name']
	user = users.find_one({ "correo": username })
	nombre = user["nombre"]
	apellido = user["apellido"]
	nombreCompleto = nombre+" "+apellido	
	if user["tipo"] == "Editor":
		posts.update_one({"_id": ObjectId(request.args.get('id'))}, {"$set": {"publicado": 1}}, upsert=False)
		postUpdateado = posts.find_one({ "_id": ObjectId(request.args.get('id'))})
		titulo = postUpdateado["titulo"]
		draftPosts = list(posts.find({"publicado": 0}))	
		isAuthor = "false"
		if user["tipo"] == "Autor":
			isAuthor = "true"
		return render_template('articulosPorPublicar.html', user = session['name'], isAuthor = isAuthor, published = "true", titulo = titulo, draftPosts = json.dumps(draftPosts, default=json_util.default))
	draftPosts = list(posts.find({"publicado": 0}))	
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('articulosPorPublicar.html', user = session['name'], isAuthor = isAuthor, published = "false", draftPosts = json.dumps(draftPosts, default=json_util.default))

@app.route('/delete')
def delete():
	username = session['name']
	user = users.find_one({ "correo": username })
	nombre = user["nombre"]
	apellido = user["apellido"]
	titulo = ""
	nombreCompleto = nombre+" "+apellido
	postEliminado = posts.find_one({ "_id": ObjectId(request.args.get('id'))})
	posts.remove({"_id": ObjectId(request.args.get('id'))})
	if postEliminado:
		titulo = postEliminado["titulo"]
		draftPosts = list(posts.find({"publicado": 0}))
		isAuthor = "false"
		if user["tipo"] == "Autor":
			isAuthor = "true"
		return render_template('articulosPorPublicar.html', user = session['name'], isAuthor = isAuthor, deleted = "true", titulo = titulo, draftPosts = json.dumps(draftPosts, default=json_util.default))
	draftPosts = list(posts.find({"publicado": 0}))
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('articulosPorPublicar.html', user = session['name'], isAuthor = isAuthor, draftPosts = json.dumps(draftPosts, default=json_util.default))


@app.route('/edit')
def edit():
	username = session['name']
	user = users.find_one({ "correo": username })
	nombre = user["nombre"]
	apellido = user["apellido"]
	nombreCompleto = nombre+" "+apellido
	post = posts.find_one({"_id": ObjectId(request.args.get('id'))})
	titulo = post["titulo"]
	resumen = post["resumen"]
	imagen = post["imagen"]
	clave = post["clave"]
	contenido = post["contenido"]
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('editarArticulo.html', user = session['name'], isAuthor = isAuthor, titulo = titulo, resumen = resumen, imagen = imagen, clave = clave, contenido = contenido)

@app.route('/editar', methods=['POST'])
def editar():
	username = session['name']
	user = users.find_one({ "correo": username })
	nombre = user["nombre"]
	apellido = user["apellido"]
	nombreCompleto = nombre+" "+apellido
	titulo = request.form.get('titulo')
	resumen = request.form.get('resumen')
	file = request.files['pic']
	if file:
		filename = secure_filename(file.filename)
		imagen = filename
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	clave = request.form.get('clave')
	contenido = request.form.get('contenido')
	#No puedes editar un post que no es tuyo si eres Autor
	post = posts.find_one({"_id": ObjectId(request.form.get('id_post'))})
	if user["tipo"] == "Autor" and post["nombre"] != nombreCompleto:
		draftPosts = list(posts.find({"publicado": 0}))
		isAuthor = "false"
		if user["tipo"] == "Autor":
			isAuthor = "true"
		return render_template('articulosPorPublicar.html', user = session['name'], isAuthor = isAuthor, edited = "false", draftPosts = json.dumps(draftPosts, default=json_util.default))
	posts.update_one({"_id": ObjectId(request.form.get('id_post'))}, {"$set": {"titulo": titulo, "resumen": resumen, "imagen": imagen, "clave": clave, "contenido": contenido}}, upsert=False)
	#Si ya no lo ha editado lo inserto como nuevo editor
	post = posts.find_one({"_id": ObjectId(request.form.get('id_post'))})
	if not nombreCompleto in post["editores"]:
		posts.update_one({"_id": ObjectId(request.form.get('id_post'))}, {"$push": {"editores": nombreCompleto}})
	postUpdateado = posts.find_one({ "_id": ObjectId(request.form.get('id_post'))})
	titulo = postUpdateado["titulo"]
	draftPosts = list(posts.find({"publicado": 0}))
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('articulosPorPublicar.html', user = session['name'], isAuthor = isAuthor, edited = "true", titulo = titulo, draftPosts = json.dumps(draftPosts, default=json_util.default))

@app.route('/crear', methods=['POST'])
def crear():
	username = session['name']
	titulo = request.form.get('titulo')
	resumen  = request.form.get('resumen')
	file = request.files['pic']
	if file:
		filename = secure_filename(file.filename)
		avatar = filename
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	clave = request.form.get('clave')
	contenido = request.form.get('contenido')
	user = users.find_one({ "correo": username })
	nombre = user["nombre"]
	apellido = user["apellido"]
	nombreCompleto = nombre+" "+apellido
	fechaPublic = time.strftime("%d/%m/%Y")
	publicado = 0
	if user["tipo"] == "Autor":	
		posts.insert_one({"titulo": titulo, "resumen": resumen, "imagen": avatar, "clave": clave, "contenido": contenido, "nombre": nombreCompleto, "fecha": fechaPublic, "publicado": publicado, "editores": []})
		draftPosts = list(posts.find({"publicado": 0}))
		isAuthor = "false"
		if user["tipo"] == "Autor":
			isAuthor = "true"
		return render_template('articulosPorPublicar.html', user = session['name'], isAuthor = isAuthor, created = "true", draftPosts = json.dumps(draftPosts, default=json_util.default))
	draftPosts = list(posts.find({"publicado": 0}))
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('articulosPorPublicar.html', user = session['name'], isAuthor = isAuthor, created = "false", draftPosts = json.dumps(draftPosts, default=json_util.default))

@app.route('/register', methods=['POST'])
def register():
	nombre = request.form.get('nombre')
	apellido  = request.form.get('apellido')
	correo = request.form.get('correo')
	fechaNac = request.form.get('fechaNac')
	file = request.files['avatar']
	if file:
		filename = secure_filename(file.filename)
		avatar = filename
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	pais = request.form.get('pais')
	tipo = request.form.get('tipo')
	descripcion = request.form.get('descripcion')
	password = request.form.get('password1')
	fechaPublic = time.strftime("%d/%m/%Y")
	todaysPosts = list(posts.find({"fecha": fechaPublic, "publicado": 1}))
	if users.find_one({ "correo": correo }):
		return render_template('articulosDeHoyNoSesion.html', error2= "true", todaysPosts = json.dumps(todaysPosts, default=json_util.default))
	users.insert_one({"nombre": nombre, "apellido": apellido, "correo": correo, "fechaNac": fechaNac, "avatar": avatar, "pais": pais, "tipo": tipo, "descripcion": descripcion, "pass": password, "favoritos": []})
	return render_template('articulosDeHoyNoSesion.html', reg = "true", todaysPosts = json.dumps(todaysPosts, default=json_util.default))

@app.route('/articulo', methods=['GET'])
def article():
	username = session['name']
	articulo = posts.find_one({ "_id": ObjectId(request.args.get('id'))})
	titulo = articulo["titulo"]
	nombre = articulo["nombre"]
	editores = ', '.join(articulo["editores"])
	fechaPublic = articulo["fecha"]
	resumen = articulo["resumen"]
	contenido = articulo["contenido"]
	clave = articulo["clave"]
	imagen = articulo["imagen"]
	user = users.find_one({ "correo": username })
	isReader = "false"
	if user["tipo"] == "Lector":
		isReader = "true"
	isFavorite = "false"
	if users.find_one({"correo": username, "favoritos": {"$elemMatch": {"$eq": ObjectId(request.args.get('id'))}}}):
		isFavorite = "true"
	allComents = list(comments.find({"id_article": articulo}))
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('articuloX.html', user = username, isAuthor = isAuthor, isFavorite = isFavorite, isReader = isReader, clave = clave, titulo = titulo, id_article = request.args.get('id'), nombre = nombre, imagen = imagen, editores = editores, fecha = fechaPublic, resumen = resumen, contenido = contenido, allComents = json.dumps(allComents, default=json_util.default))

@app.route('/articuloNS', methods=['GET'])
def articleNS():
	allComents = list(comments.find())
	articulo = posts.find_one({ "_id": ObjectId(request.args.get('id'))})
	titulo = articulo["titulo"]
	nombre = articulo["nombre"]
	editores = ', '.join(articulo["editores"])
	fechaPublic = articulo["fecha"]
	resumen = articulo["resumen"]
	contenido = articulo["contenido"]
	clave = articulo["clave"]
	imagen = articulo["imagen"]
	allComents = list(comments.find({"id_article": articulo}))
	return render_template('articuloXNoSesion.html', user = "false", clave = clave, titulo = titulo, nombre = nombre, imagen = imagen, editores = editores, fecha = fechaPublic, resumen = resumen, contenido = contenido, allComents = json.dumps(allComents, default=json_util.default))

@app.route('/comment', methods=['POST'])
def comment():
	username = session['name']
	articulo = posts.find_one({ "_id": ObjectId(request.args.get('id'))})
	user = users.find_one({ "correo": username })
	nombre = user["nombre"]
	apellido = user["apellido"]
	nombreCompleto = nombre+" "+apellido
	titulo = articulo["titulo"]
	nombre = articulo["nombre"]
	editores = ', '.join(articulo["editores"])
	fechaPublic = articulo["fecha"]
	resumen = articulo["resumen"]
	contenido = articulo["contenido"]
	clave = articulo["clave"]
	imagen = articulo["imagen"]
	avatar = user["avatar"]
	isReader = "false"
	if user["tipo"] == "Lector":
		isReader = "true"
	isFavorite = "false"
	if users.find_one({"correo": username, "favoritos": {"$elemMatch": {"$eq": ObjectId(request.args.get('id'))}}}):
		isFavorite = "true"
	fechaPublic = time.strftime("%d/%m/%Y")
	content = request.form.get('content')
	comments.insert_one({"id_article": articulo, "nombre": nombreCompleto, "fecha": fechaPublic, "contenido": content, "avatar": avatar})
	allComents = list(comments.find({"id_article": articulo}))
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('articuloX.html', user = username, isAuthor = isAuthor, isFavorite = isFavorite, isReader = isReader, id_article = request.args.get('id'), clave = clave, titulo = titulo, nombre = nombre, imagen = imagen, editores = editores, fecha = fechaPublic, resumen = resumen, contenido = contenido, allComents = json.dumps(allComents, default=json_util.default))

@app.route('/addFavorite')
def addFavorite():
	username = session['name']
	articulo = posts.find_one({ "_id": ObjectId(request.args.get('id'))})
	user = users.find_one({ "correo": username })
	nombre = user["nombre"]
	apellido = user["apellido"]
	nombreCompleto = nombre+" "+apellido
	titulo = articulo["titulo"]
	nombre = articulo["nombre"]
	editores = ', '.join(articulo["editores"])
	fechaPublic = articulo["fecha"]
	resumen = articulo["resumen"]
	contenido = articulo["contenido"]
	clave = articulo["clave"]
	imagen = articulo["imagen"]
	avatar = user["avatar"]
	isReader = "false"
	if user["tipo"] == "Lector":
		isReader = "true"
	fechaPublic = time.strftime("%d/%m/%Y")
	content = request.form.get('content')
	users.update_one({"correo": username}, {"$push": {"favoritos": ObjectId(request.args.get('id'))}})
	isFavorite = "false"
	if users.find_one({"correo": username, "favoritos": {"$elemMatch": {"$eq": ObjectId(request.args.get('id'))}}}):
		isFavorite = "true"
	allComents = list(comments.find({"id_article": articulo}))
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('articuloX.html', user = username, isAuthor = isAuthor, isFavorite = isFavorite, isReader = isReader, id_article = request.args.get('id'), clave = clave, titulo = titulo, nombre = nombre, imagen = imagen, editores = editores, fecha = fechaPublic, resumen = resumen, contenido = contenido, allComents = json.dumps(allComents, default=json_util.default))


@app.route('/removeFavorite')
def removeFavorite():
	username = session['name']
	articulo = posts.find_one({ "_id": ObjectId(request.args.get('id'))})
	user = users.find_one({ "correo": username })
	nombre = user["nombre"]
	apellido = user["apellido"]
	nombreCompleto = nombre+" "+apellido
	titulo = articulo["titulo"]
	nombre = articulo["nombre"]
	editores = ', '.join(articulo["editores"])
	fechaPublic = articulo["fecha"]
	resumen = articulo["resumen"]
	contenido = articulo["contenido"]
	clave = articulo["clave"]
	imagen = articulo["imagen"]
	avatar = user["avatar"]
	isReader = "false"
	if user["tipo"] == "Lector":
		isReader = "true"
	fechaPublic = time.strftime("%d/%m/%Y")
	content = request.form.get('content')
	users.update_one({"correo": username}, {"$pull": {"favoritos": ObjectId(request.args.get('id'))}})
	isFavorite = "false"
	if users.find_one({"correo": username, "favoritos": {"$elemMatch": {"$eq": request.args.get('id')}}}):
		isFavorite = "true"	
	allComents = list(comments.find({"id_article": articulo}))
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('articuloX.html', user = username, isAuthor = isAuthor, isReader = isReader, isFavorite = isFavorite, id_article = request.args.get('id'), clave = clave, titulo = titulo, nombre = nombre, imagen = imagen, editores = editores, fecha = fechaPublic, resumen = resumen, contenido = contenido, allComents = json.dumps(allComents, default=json_util.default))

@app.route('/profile')
def profile():
	username = session['name']
	user = users.find_one({ "correo": username })
	nombre = user["nombre"]
	apellido = user["apellido"]
	correo = user['correo']
	fechaNac = user['fechaNac']
	avatar = user['avatar']
	pais = user['pais']
	tipo = user['tipo']
	descripcion = user['descripcion']
	password = user['pass']
	isReader = "false"
	if user["tipo"] == "Lector":
		isReader = "true"
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('editarPerfil.html', isAuthor = isAuthor, nombre = nombre, isReader = isReader, apellido = apellido, correo = correo, fechaNac = fechaNac, avatar = avatar, pais = pais, tipo = tipo, descripcion = descripcion, password = password)

@app.route('/updateProfile', methods=['POST'])
def updateProfile():
	username = session['name']
	user = users.find_one({ "correo": username })
	nombre = user["nombre"]
	apellido = user["apellido"]
	nombreCompletoViejo = nombre+" "+apellido
	nombre = request.form.get('nombre')
	apellido  = request.form.get('apellido')	
	correo = request.form.get('correo')
	fechaNac = request.form.get('fechaNac')
	file = request.files['pic']
	if file:
		filename = secure_filename(file.filename)
		avatar = filename
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	pais = request.form.get('pais')
	descripcion = request.form.get('descripcion')
	password = request.form.get('password2')
	users.update_one({"correo": username}, {"$set": {"nombre": nombre, "apellido": apellido, "correo": correo, "fechaNac": fechaNac, "avatar": avatar, "pais": pais, "descripcion": descripcion, "pass": password}}, upsert=False)
	session['name'] = correo
	username = session['name']
	user = users.find_one({ "correo": username })
	nombre = user["nombre"]
	apellido = user["apellido"]
	nombreCompleto = nombre+" "+apellido	
	correo = user['correo']
	fechaNac = user['fechaNac']
	avatar = user['avatar']
	#FALTA UPDATEAR EL NOMBRE DEL AUTOR EN LOS POSTS
	comments.update({"nombre": nombreCompletoViejo}, {"$set": {"nombre": nombreCompleto, "avatar": avatar}}, upsert=False, multi=True)
	pais = user['pais']
	tipo = user['tipo']
	descripcion = user['descripcion']
	password = user['pass']
	isReader = "false"
	if user["tipo"] == "Lector":
		isReader = "true"
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('editarPerfil.html', isAuthor = isAuthor, updated = "true", isReader = isReader, nombre = nombre, apellido = apellido, correo = correo, fechaNac = fechaNac, avatar = avatar, pais = pais, tipo = tipo, descripcion = descripcion, password = password)

@app.route('/favorites')
def favorites():
	username = session['name']
	user = users.find_one({ "correo": username })
	nombre = user["nombre"]
	apellido = user["apellido"]
	nombreCompleto = nombre+" "+apellido
	favoritePosts = user["favoritos"]
	isReader = "false"
	if user["tipo"] == "Lector":
		isReader = "true"
	thosePosts = list(posts.find({"_id": {"$in":favoritePosts}}))
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('articulosFavoritos.html', isAuthor = isAuthor, user = session['name'], isReader = isReader, thosePosts = json.dumps(thosePosts, default=json_util.default))

@app.route('/removeFavoriteList')
def removeFavoriteList():
	username = session['name']	
	users.update_one({"correo": username}, {"$pull": {"favoritos": ObjectId(request.args.get('id'))}})
	user = users.find_one({ "correo": username })
	nombre = user["nombre"]
	apellido = user["apellido"]
	nombreCompleto = nombre+" "+apellido
	favoritePosts = user["favoritos"]
	isReader = "false"
	if user["tipo"] == "Lector":
		isReader = "true"
	thosePosts = list(posts.find({"_id": {"$in":favoritePosts}}))
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
	return render_template('articulosFavoritos.html', isAuthor = isAuthor, user = session['name'], isReader = isReader, thosePosts = json.dumps(thosePosts, default=json_util.default))

@app.route('/search', methods=['POST'])
def search():
	username = session['name']	
	user = users.find_one({ "correo": username })
	buscar  = request.form.get('buscar')
	isReader = "false"
	if user["tipo"] == "Lector":
		isReader = "true"
	thosePosts = list(posts.find({"$or": [{"fecha": {"$regex": buscar}},{"titulo": {"$regex": buscar}},{"nombre": {"$regex": buscar}},{"clave": {"$regex": buscar}}], "publicado": 1}))
	return render_template('articulosBuscados.html', user = session['name'], isReader = isReader, thosePosts = json.dumps(thosePosts, default=json_util.default))

@app.route('/myArticles')
def myArticles():
	allPosts = list(posts.find({"publicado": 1}))
	username = session['name']	
	user = users.find_one({ "correo": username })
	nombre = user["nombre"]
	apellido = user["apellido"]
	nombreCompleto = nombre+" "+apellido
	isReader = "false"
	if user["tipo"] == "Lector":
		isReader = "true"
	isAuthor = "false"
	if user["tipo"] == "Autor":
		isAuthor = "true"
		allPosts = list(posts.find({"publicado": 1, "nombre": nombreCompleto}))
	if user["tipo"] == "Editor":
		isAuthor = "false"
		allPosts = list(posts.find({"publicado": 1, "editores": {"$in" : [nombreCompleto]}}))
	return render_template('articulosPublicados.html', isAuthor = isAuthor, isReader = isReader, allPosts = json.dumps(allPosts, default=json_util.default))

if __name__ == '__main__':
	app.debug = True
	app.run()