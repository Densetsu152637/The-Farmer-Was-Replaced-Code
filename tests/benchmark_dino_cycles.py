import sys,random,statistics
import ast
import json
import argparse
from collections import deque
from pathlib import Path
sys.path.insert(0,'tests')
from test_dino_routes import SnakeSimulation

def cycle(n,kind,layout_seed=17):
 m=n//2
 rng=random.Random(layout_seed)
 edges=[]; visited={(0,0)}; frontier=[(0,0)]
 while len(visited)<m*m:
  if kind=='dfs': a=frontier[-1]
  else: a=rng.choice(frontier)
  opts=[(a[0]+dx,a[1]+dy) for dx,dy in ((1,0),(0,1),(-1,0),(0,-1)) if 0<=a[0]+dx<m and 0<=a[1]+dy<m and (a[0]+dx,a[1]+dy) not in visited]
  if not opts: frontier.remove(a);continue
  b=rng.choice(opts);edges.append((a,b));visited.add(b);frontier.append(b)
 adj={}
 def link(a,b): adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
 def unlink(a,b):adj[a].remove(b);adj[b].remove(a)
 for x in range(0,n,2):
  for y in range(0,n,2):
   p=[(x,y),(x,y+1),(x+1,y+1),(x+1,y)]
   for a,b in zip(p,p[1:]+p[:1]):link(a,b)
 for a,b in edges:
  if a[0]!=b[0]:
   x=2*min(a[0],b[0])+1;y=2*a[1]
   p,q,r,s=(x,y),(x,y+1),(x+1,y),(x+1,y+1)
  else:
   x=2*a[0];y=2*min(a[1],b[1])+1
   p,q,r,s=(x,y),(x+1,y),(x,y+1),(x+1,y+1)
  unlink(p,q);unlink(r,s);link(p,r);link(q,s)
 path=[(0,0)];prev=None;cur=(0,0)
 for _ in range(n*n-1):
  nxt=next(p for p in adj[cur] if p!=prev);path.append(nxt);prev,cur=cur,nxt
 assert len(set(path))==n*n and path[0] in adj[cur]
 return path

def install(sim,path):
 d=sim.dino
 for i,(x,y) in enumerate(path):
  xx,yy=path[(i+1)%len(path)]
  d.HAM_INDEX[x][y]=i
  d.HAMILTONIAN[x][y]={(0,1):'N',(1,0):'E',(0,-1):'S',(-1,0):'W'}[(xx-x,yy-y)]


def rings(n):
 adj={}
 def link(a,b):adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
 def unlink(a,b):adj[a].remove(b);adj[b].remove(a)
 for l in range(n//2):
  h=n-1-l
  path=[(l,y) for y in range(l,h)]+[(x,h) for x in range(l,h)]+[(h,y) for y in range(h,l,-1)]+[(x,l) for x in range(h,l,-1)]
  for a,b in zip(path,path[1:]+path[:1]):link(a,b)
 for l in range(n//2-1):
  p,q,r,s=(l,l+1),(l,l+2),(l+1,l+1),(l+1,l+2)
  unlink(p,q);unlink(r,s);link(p,r);link(q,s)
 path=[(0,0)];prev=None;cur=(0,0)
 for _ in range(n*n-1):
  nxt=next(p for p in adj[cur] if p!=prev);path.append(nxt);prev,cur=cur,nxt
 assert len(set(path))==n*n and path[0] in adj[cur]
 return path


class FastSimulation(SnakeSimulation):
 def __init__(self, n, seed):
  super().__init__(n, seed)
  self.body = deque()
  self.occupied = set()
  self.cells = [(x,y) for x in range(n) for y in range(n)]

 def measure(self):
  free = [p for p in self.cells if p != self.head and p not in self.occupied]
  self.next_apple = self.rng.choice(free) if free else None
  return self.next_apple

 def move(self, direction):
  dx,dy = {'N':(0,1),'E':(1,0),'S':(0,-1),'W':(-1,0)}[direction]
  target = (self.head[0]+dx,self.head[1]+dy)
  growing = self.head == self.apple
  assert 0 <= target[0] < self.size and 0 <= target[1] < self.size
  assert target not in self.occupied or (not growing and self.body and target == self.body[0])
  if growing:
   self.apple = self.next_apple
   self.since_food = 0
  elif self.body:
   self.occupied.remove(self.body.popleft())
  if growing or self.dino.STATE['length'] > 0:
   self.body.append(self.head)
   self.occupied.add(self.head)
  self.head = target
  self.moves += 1
  self.since_food += 1
  self.max_since_food = max(self.max_since_food,self.since_food)
  return True

 def run(self):
  while self.moves <= self.size ** 4:
   if not self.dino.dino_walk():
    return len(self.body) == self.size*self.size-1
   assert self.dino.STATE['length'] == len(self.body)
   assert self.dino.TAIL['size'] == len(self.body)
   assert self.since_food <= self.size*self.size
   if self.head == self.apple:
    actual = {(x,y) for x,y in self.cells if self.dino.BODY[x][y]}
    assert actual == self.occupied
  return False


def configure(sim, cutoff, ranking):
 source = Path('src/dino_util.py').read_text()
 source = source.replace('STATE["capacity"] // 2', 'STATE["capacity"] * ' + str(cutoff))
 tree = ast.parse(source)
 tree.body = [node for node in tree.body if isinstance(node,ast.FunctionDef)
              and node.name == 'hamiltonian_shortcut_safe']
 exec(compile(tree,'<benchmark shortcut variant>','exec'),sim.dino.__dict__)
 if ranking == 'manhattan':
  sim.dino.apple_distance = lambda x,y: abs(sim.dino.STATE['apple_x']-x)+abs(sim.dino.STATE['apple_y']-y)


def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--seeds',type=int,default=8)
 parser.add_argument('--start',type=int,default=0)
 parser.add_argument('--output',default='docs/dino-cycle-benchmark.json')
 parser.add_argument('--layouts',nargs='+',default=['baseline','prim','dfs','rings'])
 parser.add_argument('--cutoffs',nargs='+',type=float,default=[0.5,0.75])
 parser.add_argument('--rankings',nargs='+',default=['cycle','manhattan'])
 args=parser.parse_args()
 results=[]
 for kind in args.layouts:
  for cutoff in args.cutoffs:
   for ranking in args.rankings:
    moves=[];failed=[]
    for seed in range(args.start,args.start+args.seeds):
     sim=FastSimulation(32,seed)
     if kind!='baseline':
      route=rings(32) if kind=='rings' else cycle(32,kind,seed+10000)
      install(sim,route)
     configure(sim,cutoff,ranking)
     try:
      success=sim.run()
     except AssertionError:
      success=False
     if success: moves.append(sim.moves)
     else: failed.append({'seed':seed,'length':len(sim.body),'moves':sim.moves})
    row={'layout':kind,'cutoff':cutoff,'ranking':ranking,'start_seed':args.start,
         'seeds':args.seeds,'mean_moves':statistics.mean(moves) if moves else None,
         'median_moves':statistics.median(moves) if moves else None,
         'moves':moves,'failures':failed}
    results.append(row)
    print({k:v for k,v in row.items() if k!='moves'},flush=True)
    Path(args.output).write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':
 main()

