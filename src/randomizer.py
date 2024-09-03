import random

'''
Micro Mages Randomizer Script
By Xanthus
Skeleton movement patch by nstbayless (NaOH).

Currently randomizes enemies, player shot distances, difficulty settings,
some enemy behavior, and some level hazards (trampolines / fans).
Also includes patch for skeletons to walk over bridges and fall.

Known issues/limitations:
- Currently if you try to randomize an already randomized patch, there will be
  an issue due to applying the same asm patches with conflicting labels, as well
  as some rom patches being added on, but not necessarily overwriting older
  rom patches. Always randomize from a fresh Base ROM until this is handled properly.

This creates a MMageEdit txt file from a vanilla file. It is incorporated into the
MMagEdit GUI.
If running this file as a standalone script rather than MMagEdit GUI:
1. Open the base rom in MMagEdit and save it as 'Micro Mages - Vanilla.txt' in the
same folder as this script.
2. Run this file as a script with `python randomizer.py`, enter a seed for randomization.
3. Then open 'Micro Mages Randomized - SEEDNAME.txt' in MMageEdit, and export the randomized romhack.
'''

# TODO Ideas:
  # Face enemies towards center of screen? (If they're not an enemy whose direction matters. Snakes/trolls/etc. should keep direction when replaced. But skeletons often face away to start.)
  # Move enemies to floor/ open space? (Wish list, this will take extra dev)
  # Randomize jumpthrough platforms to boxes and/or having open spaces
  # Randomize some empty spaces to have some jump through platforms?
  # 'wisp' is a special super-tanky enemy... might not be able to just swap these in due to difficulty without editing HP / behavior
  # Randomize whether snakes can see behind
  # Randomize eye movement / jump height / speed
  # Randomize lightning/spark to an upward fan on the floor, or some other hazard
  # randomize speed (or at what difficulties enemies move faster)
  # Randomize bone speed
  # randomize player charge shot time / damage.
  # Maybe track difficulty of the seed, make sure all randomizations don't go to higher difficulty?
  # Some ghost spawns are in walls, and maybe shouldn't be replaced
    # test for solid space, or ignore randomizing specific spawns

enemies = ['skeleton', 'bat', 'goat', 'bone', 'goblin', 'ghost', 'snake', 'troll', 'eye']
floor_enemies = ['skeleton', 'goat', 'bone', 'goblin', 'snake', 'troll', 'eye']
flight_enemies = ['bat', 'ghost']
non_flight_enemies = ['skeleton', 'bone', 'snake', 'eye']

# when these enemies are replaced, the new enemy will always maintain their direction
directional_enemies = ['goat', 'snake', 'troll']

# A 'safe' pool of enemies for replacing flying enemies (ones that fly/float or telegraph before falling like Goblin)
flight_replace_enemies = ['bat', 'ghost', 'goblin', 'goat', 'troll'] #maybe eye?

def randomize_hack(filename: str, new_filename: str, seed: str):
  random.seed(seed)

  print(f'Loading "{filename}"...')
  with open(filename, 'r') as file:
    data = file.read()

  # Split the content into lines for replacement
  data_lines = data.split('\n')
  new_data_lines = []

  print('Randomizing ...')
  for line in data_lines:
    new_line = line
    for enemy in enemies:
      if '- '+enemy in line:
        # print('found "- '+enemy+'" in "'+line+'"')
        rnd_enemy = randomize_enemy(enemy)
        new_line = new_line.replace('- '+enemy, '- '+rnd_enemy)
        # remove compressed storage on all replaced objects (may not be eligible due to X value or object, etc.)
        new_line =new_line.replace(' * x', '   x')

        # Move enemy up if randomizing from a floor enemy to a flying one
        if enemy in floor_enemies and rnd_enemy in flight_enemies:
          y_index = new_line.find(' y')+1
          y_value = int(new_line[y_index+1:y_index+4], 16)
          y_value -= 3
          new_line =  new_line[:y_index]+'y'+hex(y_value)+new_line[y_index+3:]
          # print('moving bat up :'+new_line)

        if enemy not in directional_enemies and rnd_enemy in directional_enemies:
          # Face towards center of the screen.
          # if X value is > x10, on the right side of the screen
          right_side = new_line.find(' x1')
          reverse_x_index = new_line.find('-x')
          if right_side>0 and reverse_x_index==-1 :
            new_line += ' -x'

          if right_side==-1 and reverse_x_index!=-1:
            reverse_x_index = new_line.find('-x')
            new_line = new_line[reverse_x_index:]

        # print('replaced with '+rnd_enemy)
        break
    if '- torch' in new_line:
      # 25% chance for torch to turn into ghost or bat
      if '- torch      * x0d y15' not in new_line and random.random()>.75:
        if random.random()>.5:
          new_line = new_line.replace('- torch', '- ghost')
        else:
          new_line = new_line.replace('- torch', '- bat')
        # remove compressed storage on all replaced objects (may not be eligible due to X value or object, etc.)
        new_line =new_line.replace(' * x', '   x')

    # Randomize HP from -2 to +4 (increments of 2)
    if new_line[:4]=='hp 0':
      old_hp = int(new_line[4:], 16)  # get last character, convert hex string to number
      new_hp = random.randint(-1,2)*2 + old_hp
      new_line = 'hp '+hex(new_hp)[2:]  # change to byte number format (without the '0x' in front)

    # Swap Trampolines and Fans sometimes
    # Only swap a vertical fan if it's pointing upwards (doesn't have -y pointing down)
    # Otherwise, a ceiling trampoline can push the player into the ceiling and be stuck
    if '- trampoline' in new_line and random.random()>0.75:
      new_line = new_line.replace('- trampoline', '- fanv')
    elif '- fanv' in new_line and '-y' not in new_line and random.random()>0.75:
      new_line = new_line.replace('- fanv', '- trampoline')

    # Sprite Palette randomization
    if (new_line[:3] == 'P0 ' or new_line[:3] == 'P1 '\
        or new_line[:3] == 'P2 ' or new_line[:3] == 'P3 '):

      # convert hex to int, add, convert back
      color_r = int(new_line[3:5], 16)
      color_g = int(new_line[6:8], 16)
      color_b = int(new_line[9:11], 16)

      # NES color palette indexes for black and white / gray
      blacks_or_whites = [0x00, 0x10, 0x20, 0x30, 0x0D, 0x0F, 0x1D, 0x1F, 0x2D, 0x2F, 0x3D, 0x3F]

      if color_r not in blacks_or_whites:
        color_r = clamp_palette_color(color_r+random.randint(-4,4))
        # don't randomize to black or white color.
        while color_r in blacks_or_whites:
          color_r = clamp_palette_color(color_r+random.randint(-4,4))

      if color_g not in blacks_or_whites:
        color_g = clamp_palette_color(color_g+random.randint(-4,4))
        # don't randomize to black or white color.
        while color_g in blacks_or_whites:
          color_g = clamp_palette_color(color_g+random.randint(-4,4))

      if color_b not in blacks_or_whites:
        color_b =clamp_palette_color(color_b+random.randint(-4,4))
        # don't randomize to black or white color.
        while color_b in blacks_or_whites:
          color_b = clamp_palette_color(color_b+random.randint(-4,4))

      '''
      color_r = random.randint(16,40)
      color_g = 40-int(color_r)
      color_b = 20
      '''
      new_line = f'{new_line[:2]} {hex(color_r)} {hex(color_g)} {hex(color_b)}'
      # print(new_line)

    # Map Palette randomization
    if (new_line[:3] == 'P0:' or new_line[:3] == 'P1:'\
        or new_line[:3] == 'P2:' or new_line[:3] == 'P3:'):

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

      # print(f'{new_line} - color_r: {color_r}  hex: {"{:02x}".format(color_r)}')

      # NES color palette indexes for black and white / gray
      blacks_or_whites = [0x00, 0x10, 0x20, 0x30, 0x0D, 0x0F, 0x1D, 0x1F, 0x2D, 0x2F, 0x3D, 0x3F]

      if color_r not in blacks_or_whites:
        color_r = clamp_palette_color(color_r+random.randint(-4,4))
        # don't randomize to black or white color.
        while color_r in blacks_or_whites:
          color_r = clamp_palette_color(color_r+random.randint(-4,4))

      if color_g not in blacks_or_whites:
        color_g = clamp_palette_color(color_g+random.randint(-4,4))
        # don't randomize to black or white color.
        while color_g in blacks_or_whites:
          color_g = clamp_palette_color(color_g+random.randint(-4,4))

      if color_b not in blacks_or_whites:
        color_b = clamp_palette_color(color_b+random.randint(-4,4))
        # don't randomize to black or white color.
        while color_b in blacks_or_whites:
          color_b = clamp_palette_color(color_b+random.randint(-4,4))

      new_line = f'{new_line[:3]} {"{:02x}".format(color_r)} {"{:02x}".format(color_g)} {"{:02x}".format(color_b)}'
      # print(new_line)

    # Enable Mapper extension mod
    new_line =new_line.replace('"mapper-extension": false', '"mapper-extension": true')

    new_data_lines.append(new_line)

  print('Applying ROM Patches ...')
  apply_rompatches(new_data_lines)

  # merge back into a single string for writing
  new_data = '\n'.join(new_data_lines)
  print(f'Saving randomized file: "{new_filename}" ...')
  with open(new_filename, 'w') as out_file:
    out_file.write(new_data)


def apply_rompatches(new_data_lines: list):
  # This will need to add custom ASM code / patches
  # Find the line where patches should go, insert after the commented lines
  for i in range(len(new_data_lines)-1,0,-1):
    if '-- patch --' in new_data_lines[i]:
      rom_patch_line = i+1
      break

  # Randomize spell/ shot length
  # Ensure at least one of the shots remains long for bosses (at least 20? might need to test)
  # CCE2 - Length of normal shot, 0x25
  # CCE3 : lenght of long shot, 0x29
  spell1_timer = 0x25+random.randint(-5,1)*5
  spell2_timer = 0x27+random.randint(-5,1)*5
  if spell1_timer<20 and spell2_timer<20:
    if random.random()>0.5:
      spell1_timer = 20
    else:
      spell2_timer = 20
  new_data_lines.insert(rom_patch_line, f'rampatch CCE2 {"{:02x}".format(spell1_timer)} {"{:02x}".format(spell2_timer)} #Custom spell timers')

  # Random chance for super fast skeletons
  if random.random()>0.75:
    new_data_lines.insert(rom_patch_line, f'rampatch EB2D EA EA #Fast Skeletons')  # NOP NOP instructions

  # Random chance for skeletons to always throw bones
  if random.random()>0.75:
    new_data_lines.insert(rom_patch_line, f'rampatch EB31 EA EA #Skeletons always throw bones')  # NOP NOP instructions

  # Randomize player jump timer slightly (Default 0xA)
  random_jump_timer = 0xA + random.randint(-3,3)
  new_data_lines.insert(rom_patch_line, f'rampatch D392 {"{:02x}".format(random_jump_timer)} # Random jump timer')

  # Randomize player charge timer
  # D53A sets initial value for charge timer, which is stored and incremented at 0x3A0. When it reaches 0x80 (the byte is no longer positive),
  # then you can release for charge shot.
  random_charge_time = 0x49 + random.randint(-30,20)
  new_data_lines.insert(rom_patch_line, f'rampatch D53A {"{:02x}".format(random_charge_time)} # Random charge timer')

  apply_skeleton_movement_patch(new_data_lines)
  apply_random_difficulty(new_data_lines)


def apply_random_difficulty(new_data_lines: list):
  """ Randomizes difficulty settings
  00D912 .Difficulty_normalModeData - 82 63 02 98 02 80 19 B0 58 B4 8C 98 28 82 80 40 70 04 0C 1E 64
  00D927 .Difficulty_hardModeData - 2D 4F 03 BA 03 60 00 FF 74 73 4C A8 1B 52 80 60 74 08 10 34 7C
  00D93C .Difficulty_hellModeData - 01 42 04 D7 04 57 00 FF A8 69 4C D0 10 46 B0 70 A8 0B 13 60 A0

  Each Difficulty data set contains the following list (gets copied to these location in RAM)
  - Length 0x14
  000568 .Difficulty_goatIdleTicks
  000569 .Difficulty_goatBubbleDelay
  00056A .Difficulty_goatBubbleCount
  00056B .Difficulty_goatBubbleVelocity
  00056C .Difficulty_goatBubbleSubVyFrac
  00056D .Difficulty_trollIdleTicks
  00056E .Difficulty_goblinJumpDelay
  00056F .Difficulty_warthogVxFrac
  000570 .Difficulty_ghostVFracLimit
  000571 .Difficulty_boss2SparkDelay
  000572 .Difficulty_boss2BarrelBaseDelay
  000573 .Difficulty_boss2BarrelVelocity
  000575 .Difficulty_boss3SpellDelay
  000576 .Difficulty_boneVelocity
  000577 .Difficulty_batVelocity
  000578 .Difficulty_knightBatVelocity
  000579 .Difficulty_willowispAccelerationSlow
  00057A .Difficulty_willowispAccelerationFast
  00057B .Difficulty_willowispVFracLimitSlow
  00057C .Difficulty_willowispVFracLimitFast
  """

  ADDR_DIFFICULTY_NORMAL = 0x00D912
  ADDR_DIFFICULTY_HARD = 0x00D927
  ADDR_DIFFICULTY_HELL = 0x00D93C

  DEFAULT_NORMAL = [0x82,0x63,0x02,0x98,0x02,0x80,0x19,0xB0,0x58,0xB4,0x8C,0x98,0x28,0x82,0x80,0x40,0x70,0x04,0x0C,0x1E,0x64]
  DEFAULT_HARD = [0x2D,0x4F,0x03,0xBA,0x03,0x60,0x00,0xFF,0x74,0x73,0x4C,0xA8,0x1B,0x52,0x80,0x60,0x74,0x08,0x10,0x34,0x7C]
  DEFAULT_HELL = [0x01,0x42,0x04,0xD7,0x04,0x57,0x00,0xFF,0xA8,0x69,0x4C,0xD0,0x10,0x46,0xB0,0x70,0xA8,0x0B,0x13,0x60,0xA0]

  # modify each setting to 50%-150%. Use the same percentage for the same setting across difficulties.
  # For example, make bats 130% speed across the entire game relative to current game mode.
  random_percents = [random.randint(50,150)/100 for _ in range(len(DEFAULT_NORMAL))]

  modded_normal = []
  modded_hard = []
  modded_hell = []

  for i in range(len(DEFAULT_NORMAL)):
    rnd_normal = clamp_to_byte(int(DEFAULT_NORMAL[i]*random_percents[i]))
    rnd_hard = clamp_to_byte(int(DEFAULT_HARD[i]*random_percents[i]))
    rnd_hell = clamp_to_byte(int(DEFAULT_HELL[i]*random_percents[i]))
    modded_normal.append(rnd_normal)
    modded_hard.append(rnd_hard)
    modded_hell.append(rnd_hell)

  # Write rompatches for each in the patch section
  i = 0
  for line in new_data_lines:
    if line == '-- patch --':
      break
    i+=1

  new_data_lines.insert(i+1, "; Custom Difficulty settings")
  i+=1

  # Write lines, without 0x in front of hex
  new_data_lines.insert(i+1,"rampatch "+format(ADDR_DIFFICULTY_NORMAL, 'x')+" "+' '.join([format(x, 'x') for x in modded_normal]))
  new_data_lines.insert(i+2,"rampatch "+format(ADDR_DIFFICULTY_HARD, 'x')+" "+' '.join([format(x, 'x') for x in modded_hard]))
  new_data_lines.insert(i+3,"rampatch "+format(ADDR_DIFFICULTY_HELL, 'x')+" "+' '.join([format(x, 'x') for x in modded_hell]))

  return new_data_lines


def apply_skeleton_movement_patch(new_data_lines: list):
  # Skeleton movement patch by nstbayless (NaOH).

  # Find where ASM section is, insert patch code after
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

def randomize_enemy(enemy: str):
  possible_enemies = enemies.copy()
  # if a bat or ghost, don't randomize to skeleton or bone (they don't fall)
  if enemy in flight_enemies:
    # Don't drop enemies that are too quick to respond to on the players head
    # TODO: Remove Skeleton once I finish ceiling skeleton patch
    for non_flight_enemy in non_flight_enemies:
      possible_enemies.remove(non_flight_enemy)

  rnd_enemy = random.choice(possible_enemies)
  return rnd_enemy

def clamp_to_byte(n):
  return max(min(255,n),0)

def clamp_palette_color(n):
  'should be values between 0x0 and 0x40 (inclusive)'
  return max(0x0,min(0x40,n))

# Run randomizer as a script if this file is launched directly
if __name__ == '__main__':
  seed = input('Seed: ')
  filename = './Micro Mages - Vanilla.txt'
  new_filename = f'./Micro Mages Randomized - {seed}.txt'

  randomize_hack(filename, new_filename, seed)
