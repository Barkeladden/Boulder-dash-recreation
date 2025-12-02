# -*- coding: utf-8 -*-
"""
Created on Wed Nov  1 09:34:54 2023

@author: Barkn
"""
from random import choice

blocks = ['.', ' ', '.', ' ', 'b', 'B', 'B', ' ', '.', '.', '.', '.', 'G']
for n in range(15):
    print('e', end='')
    for i in range(30):
        print (choice(blocks), end='')
    print('e')
    