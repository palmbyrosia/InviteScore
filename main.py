import discord
import os
import time
import discord.ext
from discord.utils import get
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions,  CheckFailure, check
import sqlite3

intents = discord.Intents().all()
client = discord.Client()

client = commands.Bot(command_prefix = '-', intents = intents) #put your own prefix here

db = sqlite3.connect('main.sqlite',timeout=10)
cursor = db.cursor()
cursor.execute('''
        CREATE TABLE IF NOT EXISTS main(
            user_id INTEGER,
            score INTEGER
        )
    ''')
cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests(
            sender_id INTEGER,
            invitee_id INTEGER
        )
    ''')
db.commit()

def create_score(score):
  sql = ''' INSERT INTO main(user_id, score)
              VALUES(?,0) '''
  cursor.execute(sql, score)
  db.commit()
  return cursor.lastrowid

def create_request(request, ctx):
  sql = ''' 
    SELECT 
      sender_id
    FROM
      requests
    WHERE
      invitee_id = ?; 
    ''' 
  cursor.execute(sql, (request[1],))
  if not len(cursor.fetchall()) == 0:
    return None
  sql = ''' INSERT INTO requests(sender_id, invitee_id)
              VALUES(?,?) '''
  cursor.execute(sql, request)
  db.commit()
  return cursor.lastrowid

def log():
  sql = ''' SELECT * FROM main '''
  cursor.execute(sql)
  print("LOGGING MAIN SCORE TABLE")
  for i in cursor.fetchall():
    print(i)
  print("---- log done ----")

  sql = ''' SELECT * FROM requests '''
  cursor.execute(sql)
  print("LOGGING FROM INVITE REQUEST TABLE")
  for i in cursor.fetchall():
    print(i)
  print("---- log done ----")

@client.event
async def on_ready():
    print("bot online")
    log() 

@client.event
async def on_member_join(member):
  sql = ''' 
    SELECT 
      sender_id
    FROM
      requests
    WHERE
      invitee_id = ?; 
    '''
  person = str(member.name)+'#'+str(member.discriminator)
  vals=(person,)
  cursor.execute(sql, vals)
  rows = cursor.fetchall()
  for i in rows:
    sql = ''' 
    SELECT 
      score
    FROM
      main
    WHERE
      user_id = ?; 
    '''
    vals = (i[0],)
    cursor.execute(sql, vals)
    scores = cursor.fetchall()
    score = 0
    for j in scores:
      score=j[0]+1
    sql = '''
      UPDATE main
      SET
        score = ?
      WHERE
        user_id = ?
    '''
    vals=(score, i[0])
    cursor.execute(sql, vals)
    db.commit()
    log()

@client.command()
async def invites(ctx, member  : discord.Member = None):
  m = member
  if member == None:
    m=ctx.message.author

  print(m.id)
  sql = ''' 
    SELECT 
      score
    FROM 
      main
    WHERE
      user_id = ?; 
    '''
  vals = (m.id,)
  cursor.execute(sql, vals)
  score = cursor.fetchall()
  if len(score) == 0:
    await ctx.send("This user has not invited anyone")
  else:
    await ctx.send("This person's score is: " + str(score[0][0]))
  
@client.command()
async def lb(ctx):
  embedVar = discord.Embed(title="Global Invite Leaderboard", color=0x00ff00)
  position = 1
  sql = ''' 
    SELECT 
      *
    FROM 
      main 
    '''
  cursor.execute(sql)
  scr = cursor.fetchall()
  users = "N/A"
  scores = "N/A"
  for i in scr:
    if position == 1:
      member = ctx.message.guild.get_member(int(i[0]))
      users = f'{position}. {member.name}#{member.discriminator}\n'
      scores = f'{i[1]}\n'
    else:
      member = ctx.message.guild.get_member(int(i[0]))
      users += f'{position}. {member.name}#{member.discriminator}\n'
      scores += f'{i[1]}\n'
    position+=1
  embedVar.add_field(name="User", value=users, inline=True)
  embedVar.add_field(name="Score", value=scores, inline=True)
  await ctx.send(embed=embedVar)
@client.command()
async def inv(ctx, membertag=None):
  await ctx.send("Processing... (Remember, this will only work if the member tag (eg. username#0000) you passed in is valid)")
  if membertag:
    invite = await ctx.channel.create_invite()
    sql = ''' 
    SELECT 
      score
    FROM
      main
    WHERE
      user_id = ?; 
    ''' 
    vals = (ctx.message.author.id,)
    cursor.execute(sql, vals)
    if len(cursor.fetchall()) == 0:
      create_score((ctx.message.author.id,))
    req = create_request((ctx.message.author.id, membertag), ctx)
    if not req:
      await ctx.send("You cannot invite a member who as already been invited for points")
      return
    log()
    await ctx.send('Request Succesful, here is your invite: ' + invite.url)
  else:
    await ctx.send('Please pass in a member tag (eg. username#0000) in to the command like ```inv <member tag>```')


client.run(os.getenv("TOKEN")) #get your bot token and make a file called ".env" then inside the file write TOKEN=put your api key here example in env.txt
#The instructions are also there in example.env