# Micro Mages randomizer script
# By Xanthus

# Creates a MMageEdit txt file from a vanilla file.
# Before using this script, open the base rom and save it as 'Micro Mages - Vanilla.txt'
# Run this script, then open `Micro Mages - Randomized.txt` in MMageEdit for a randomized romhack

# Currently randomizes enemies, player shot distances, some enemy behavior,
# and some level hazards (trampolines / fans).
# Also includes patch for skeletons to walk over bridges and fall

# Map/level editing Ideas:
  # Fan slightly blowing through floor, messes up movement
  # unhittable enemies shooting projectils

# TODO Ideas:
  # Input a specific seed
  # X Replace 'torch' with 'ghost' sometimes? or other enemies
  # Face enmeies towards center of screen? (If they're not an enemy whose direction matters. Snakes/trolls/etc. should keep direction when replaced. But skeletons often face away to start.)
  # Move enemies to floor/ open space? (Wish list, this will take extra dev)
  # Randomize jumpthrough platforms to boxes and/or having open spaces
  # Randomize some empty spaces to have some jump through platforms?
  # 'wisp' is a special super-tanky enemy... might not be able to just swap these in due to difficulty without editing HP / behavior
  # Randomize whether snakes can see behind
  # Randomize eye movement / jump height / speed
  # Randomize lightning/spark to an upward fan on the floor?
  # randomize speed (or at what difficulties enemies move faster)
  # Randomize bone speed
  # Maybe track difficulty of the seed, make sure all randomizations don't go to higher difficulty?

# TODO ISSUES:
  # - Spawning issues
    # - Current temporary solution, removing forced compressed storage (*) on all objects
  # - Some ghost spawns are in walls, and maybe shouldn't be replaced
    # - test for solid space, or ignore randomizing specific spawns
  # X (temp fixed) bats turning into skeletons / bones which stand still in midair
  # X When bats replace enemies on the floor, they are too easy. (move them up in the air)


import random

filename = './Micro Mages - Vanilla.txt'
new_filename = './Micro Mages - Randomized.txt'

with open(filename, 'r') as file:
  data = file.read()


# Split the content into lines for replacement
data_lines = data.split('\n')


enemies = ['skeleton', 'bat', 'goat', 'bone', 'goblin', 'ghost', 'snake', 'troll', 'eye']
floor_enemies = ['skeleton', 'goat', 'bone', 'goblin', 'snake', 'troll', 'eye']
flight_enemies = ['bat', 'ghost']

# Maybe a 'safe' pool of enemies for replacing flying enemies (on ceiling, they'll drop down, hard to avoid if climbing close to the top)
flight_replace_enemies = ['bat', 'ghost', 'gobline', 'goat', 'troll'] #maybe eye?

def randomize_enemy(enemy):
  possible_enemies = enemies.copy()
  # if a bat or ghost, don't randomize to skeleton or bone (they don't fall)
  if enemy in flight_enemies:
    # No longer needed due to new skeleton patch: possible_enemies.remove('skeleton')
    # however, may want to include so they don't fall on your head when spawning

    possible_enemies.remove('bone')

  rnd_enemy = random.choice(possible_enemies)
  return rnd_enemy

def apply_skeleton_movement_patch(new_data_lines: list):
  # Find where ASM is

  # insert everything after
  skeleton_movement_patch = '''
  ; can probably push this earlier...
  ; this is within the region of the original rom where level data was stored
  ; but the mapper hack only uses the start of that space, well before e600
  org $e600

  skeleton_new_walkState:
      lda #$00
      ldy #$04
      jsr $A138 ; MapCollision_canActorPassSFA
      beq skeleton_new_walkState_maybe_gravity

  skeleton_new_walkState_return_detour:
      ; original code
      ldy #$01
      jsr $8811
      jmp $EB2D ; return from detour

  skeleton_new_walkState_maybe_gravity:
      lda #$FC
      ldy #$04
      jsr $A138 ; MapCollision_canActorPassSFA
      bne skeleton_new_walkState_dex

      lda #$04
      tay
      jsr $A138 ; MapCollision_canActorPassSFA
      sec
      bne skeleton_new_walkState_inx

      jsr $AA0B ; gravity
  skeleton_new_walkState_earlyFinish:
      jmp $D8C9 ; barrel update

  skeleton_new_walkState_inx:
      lda #$1
      adc $4A, X ; objx
      sta $4A, X ; objx
      jmp skeleton_new_walkState_return_detour

  skeleton_new_walkState_dex:
      lda $4A, X ; objx
      sbc #$2
      sta $4A, X ; objx
      jmp skeleton_new_walkState_return_detour

  ChangeDirection_UnlessBigSkeletonOnBridge:
      ; id
      lda $200,X
      cmp #$A ; large skeleton
      bne ChangeDirection_Yes

      lda #$00
      ldy #$09
      jsr $A118 ; MapCollision__getActorTileFlagsDxDy
      and #$4
      beq ChangeDirection_Yes

  ChangeDirection_No:
      ; ...unless next to boxes
      lda #$04
      ldy #$00
      jsr $A138 ; MapCollision_canActorPassSFA
      bne ChangeDirection_Yes

      lda #$FC
      ldy #$00
      jsr $A138 ; MapCollision_canActorPassSFA
      bne ChangeDirection_Yes

      rts

  ChangeDirection_Yes:
      jmp $A872 ; change direction


  ;max $e6ee ; [end of levels, in original rom; mapper hack doesn't use this space]

  ; ---

  ; skeleton logic
  org $EB28
      jmp skeleton_new_walkState
      nop
      nop

  org $EB63
      ; skeleton do walk
      jmp ChangeDirection_UnlessBigSkeletonOnBridge'''

  skeleton_movement_patch_lines = skeleton_movement_patch.split('\n')

  i = 0
  for line in new_data_lines:
    if line == '-- asm --':
      break
    i+=1

  # move to line after asm
  i+=1

  for line in skeleton_movement_patch_lines:
    new_data_lines.insert(i+1, line)
    i+=1

  return new_data_lines

# loop through lines, replacing any occurance with any other random occurance
new_data_lines = []
print_first_line = False
sprite_palettes=0
for line in data_lines:
  new_line = line
  for enemy in enemies:
    if '- '+enemy in line:
      # print('found "- '+enemy+'" in "'+line+'"')
      rnd_enemy = randomize_enemy(enemy)
      new_line = new_line.replace('- '+enemy, '- '+rnd_enemy)
      # remove compressed storage on all objects (may not be eligible due to X value or object, etc.)
      new_line =new_line.replace(' * x', '   x')

      # Move enemy up if randomizing from a floor enemy to a flying one
      if enemy in floor_enemies and rnd_enemy in flight_enemies:
        y_index = new_line.find(' y')+1
        y_value = int(new_line[y_index+1:y_index+4], 16)
        y_value -= 3
        new_line =  new_line[:y_index]+'y'+hex(y_value)+new_line[y_index+3:]
        print('moving bat up :'+new_line)


      # print('replaced with '+rnd_enemy)
      if not print_first_line:
        old_line = line
        print_first_line = new_line
      break
  if '- torch' in line:
    # 25% chance for torch to turn into ghost or bat
    if '- torch      * x0d y15' not in line and random.random()>.75:
      if random.random()>.5:
        new_line = line.replace('- torch', '- ghost')
        # remove compressed storage on all objects (may not be eligible due to X value or object, etc.)
        new_line =new_line.replace(' * x', '   x')
      else:
        print("BAT")
        new_line = line.replace('- torch', '- bat')
        # remove compressed storage on all objects (may not be eligible due to X value or object, etc.)
        new_line =new_line.replace(' * x', '   x')
  if (new_line[:3] == 'P0 ' or new_line[:3] == 'P1 '\
      or new_line[:3] == 'P2 ' or new_line[:3] == 'P3 '): # for only changing sprite palettes

    # Sprite palettes

    # instead, do slight edits
    # P0 1C 24 20
    # P1 15 27 20
    # P2 1C 2C 20
    # P3 19 29 20

    # convert hex to int, add, convert back
    color_r = int(new_line[3:5], 16)
    color_g = int(new_line[6:8], 16)
    color_b = int(new_line[9:11], 16)

    # NES color palette indexes for black and white / gray
    blacks_or_whites = [0x00, 0x10, 0x20, 0x30, 0x0D, 0x0F, 0x1D, 0x1F, 0x2D, 0x2F, 0x3D, 0x3F]

    if color_r not in blacks_or_whites:
      color_r = max(color_r+random.randint(-4,4),0)
      # don't randomize to black or white color.
      while color_r in blacks_or_whites:
        color_r = max(color_r+random.randint(-4,4),0)

    if color_g not in blacks_or_whites:
      color_g = max(color_g+random.randint(-4,4),0)
      # don't randomize to black or white color.
      while color_g in blacks_or_whites:
        color_g = max(color_g+random.randint(-4,4),0)

    if color_b not in blacks_or_whites:
      color_b = max(color_b+random.randint(-4,4),0)
      # don't randomize to black or white color.
      while color_b in blacks_or_whites:
        color_b = max(color_b+random.randint(-4,4),0)

    '''
    color_r = random.randint(16,40)
    color_g = 40-int(color_r)
    color_b = 20
    '''
    new_line = f'{new_line[:2]} {hex(color_r)} {hex(color_g)} {hex(color_b)}'
    print(new_line)
  if (new_line[:3] == 'P0:' or new_line[:3] == 'P1:'\
      or new_line[:3] == 'P2:' or new_line[:3] == 'P3:'): # for only changing sprite palettes

    # Map palettes
    # Issue: something regarding moving black to a bright gray somehow?

    # instead, do slight edits
    # P0 1C 24 20
    # P1 15 27 20
    # P2 1C 2C 20
    # P3 19 29 20

    # convert hex to int, add, convert back
    color_r = int(new_line[4:6], 16)
    color_g = int(new_line[7:9], 16)
    color_b = int(new_line[10:12], 16)

    print(f'{new_line} - color_r: {color_r}  hex: {"{:02x}".format(color_r)}')

    # NES color palette indexes for black and white / gray
    blacks_or_whites = [0x00, 0x10, 0x20, 0x30, 0x0D, 0x0F, 0x1D, 0x1F, 0x2D, 0x2F, 0x3D, 0x3F]

    if color_r not in blacks_or_whites:
      color_r = max(color_r+random.randint(-4,4),0)
      # don't randomize to black or white color.
      while color_r in blacks_or_whites:
        color_r = max(color_r+random.randint(-4,4),0)

    if color_g not in blacks_or_whites:
      color_g = max(color_g+random.randint(-4,4),0)
      # don't randomize to black or white color.
      while color_g in blacks_or_whites:
        color_g = max(color_g+random.randint(-4,4),0)

    if color_b not in blacks_or_whites:
      color_b = max(color_b+random.randint(-4,4),0)
      # don't randomize to black or white color.
      while color_b in blacks_or_whites:
        color_b = max(color_b+random.randint(-4,4),0)

    new_line = f'{new_line[:3]} {"{:02x}".format(color_r)} {"{:02x}".format(color_g)} {"{:02x}".format(color_b)}'
    print(new_line)
    print('---')


  new_data_lines.append(new_line)

# Replace Trampolines with Fans.
for i, item in enumerate(new_data_lines):
  if '- trampoline' in item and random.random()>0.75:  # TODO: Not liking this conditional...
   new_data_lines[i] = item.replace('- trampoline', '- fanv')
  new_data_lines[i] = new_data_lines[i].replace('"mapper-extension": false', '"mapper-extension": true')

for i, item in enumerate(new_data_lines):
  # Randomize hp from -2 to +4
  if item[:4]=='hp 0':
    old_hp = int(item[4:], 16)  # get last character, convert hex string to number
    new_hp = random.randint(-1,2)*2 + old_hp
    new_data_lines[i] = 'hp '+hex(new_hp)[2:]  # change to byte number format (without the '0x' in front)

# This will need to add custom ASM code / patches
# Find the line where patches should go, insert after the commented lines
for i in range(len(new_data_lines)-1,0,-1):
  if '#rompatch' in new_data_lines[i]:
    rom_patch_line = i
    break

# Randomize spell/ shot length
# Ensure at least one of the shots remains long for bosses (at least 20? might need to test)
# CCE2 - Length of normal shot, 25
# CCE3 : lenght of long shot, 29
spell1_timer = 25+random.randint(-3,2)*5
spell2_timer = 27+random.randint(-3,2)*5
if spell1_timer<20 and spell2_timer<20:
  if random.random()>0.5:
    spell1_timer = 20
  else:
    spell2_timer = 20
new_data_lines.insert(rom_patch_line, f'rampatch CCE2 {spell1_timer} {spell2_timer} #Custom spell timers')

# Random chance for super fast skeletons
if random.random()>0.7:
  new_data_lines.insert(rom_patch_line, f'rampatch EB2D EA EA #Fast Skeletons')  # NOP NOP instructions

new_data_lines = apply_skeleton_movement_patch(new_data_lines)

# merge back into a single string for writing
new_data = '\n'.join(new_data_lines)

with open(new_filename, 'w') as out_file:
  out_file.write(new_data)

