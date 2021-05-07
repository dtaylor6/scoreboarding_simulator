# Author: Daniel Taylor (dtaylor6@umbc.edu)
import os

# integer and floating point registers initialized to value 0
REGISTERS = {"$0": 0, "$1": 0, "$2": 0, "$3": 0, "$4": 0, "$5": 0, "$6": 0,
             "$7": 0, "$8": 0, "$9": 0, "$10": 0, "$11": 0, "$12": 0,
             "$13": 0, "$14": 0, "$15": 0, "$16": 0, "$17": 0, "$18": 0,
             "$19": 0, "$20": 0, "$21": 0, "$22": 0, "$23": 0, "$24": 0,
             "$25": 0, "$26": 0, "$27": 0, "$28": 0, "$29": 0, "$30": 0,
             "$31": 0, "F0": 0, "F1": 0, "F2": 0, "F3": 0, "F4": 0,
             "F5": 0, "F6": 0, "F7": 0, "F8": 0, "F9": 0, "F10": 0, "F11": 0,
             "F12": 0, "F13": 0, "F14": 0, "F15": 0, "F16": 0, "F17": 0,
             "F18": 0, "F19": 0, "F20": 0, "F21": 0, "F22": 0, "F23": 0,
             "F24": 0, "F25": 0, "F26": 0, "F27": 0, "F28": 0, "F29": 0,
             "F30": 0, "F31": 0}

# memory locations with default values specified
MEMORY = {0: 45, 1: 12, 2: 0, 3: 0, 4: 10, 5: 135, 6: 254, 7: 127, 8: 18,
          9: 4, 10: 55, 11: 8, 12: 2, 13: 98, 14: 13, 15: 5, 16: 233,
          17: 158, 18: 167}

# how long each functional unit type takes to execute in clock cycles
FU_CONFIG = {"FP Add": 2, "FP Mult": 10, "FP Div": 40, "Int Unit": 1}

# list of supported instructions
SUPPORTED = {"L.D": 1, "S.D": 2, "LI": 3, "LW": 4, "SW": 5, "ADD": 6,
             "ADDI": 7, "ADD.D": 8, "SUB.D": 9, "SUB": 10, "MUL.D": 11,
             "DIV.D": 12}


# class TextParse: parses instructions and then runs the scoreboard
class TextParse:

    def __init__(self, file):
        self.path = file
        self.score_board = Scoreboard()

    # get instructions from text file
    def parse(self):
        file = open(self.path, "r")

        instructions = file.readlines()
        # this segments our instruction into parts
        num_inst = 0
        for inst in instructions:
            inst_split = inst.split()

            # remove commas from instruction tokens
            for i in range(len(inst_split)):
                inst_split[i] = inst_split[i].replace(',', '')

            # add instruction to scoreboard instruction list
            if len(inst_split) > 2:
                if inst_split[0] not in SUPPORTED:
                    raise ValueError(inst_split[0] + " is not a valid instruction")
                new_inst = Instruction(inst_split, inst, num_inst)
                self.score_board.insts.append(new_inst)
                num_inst += 1

    def run(self):
        self.parse()
        # keep cycling the scoreboard until all instructions finish
        while self.score_board.clock_tick() != 1:
            pass

        # print scoreboard output
        print()
        print("{:<25} {:<8} {:<8} {:<8} {:<8}".format('Instruction', 'Issue', 'Read',
                                                      'Exec', 'Write'))
        for inst in self.score_board.insts:
            print("{:<25} {:<8} {:<8} {:<8} {:<8}".format(inst.string_rep[0:-1], inst.issue,
                                                          inst.read, inst.exec, inst.write))

        print("\n------Register Values------")
        print("{:<8} {:<12} {:<15}".format('#', '$', 'F'))
        for x in range(0, 32):
            int_key = '$' + str(x)
            f_key = 'F' + str(x)
            print("{:<8} {:<12} {:<15}".format(x, REGISTERS[int_key], REGISTERS[f_key]))

        print("\n---Memory Values---")
        print("{:<8} {:<15}".format('#', 'Value'))
        for x in range(0, 19):
            print("{:<8} {:<15}".format(x, MEMORY[x]))


# class Scoreboard: performs scoreboarding with given instructions and functional units
class Scoreboard:

    def __init__(self):
        self.units = []  # list of FunctionalUnit objects
        self.insts = []  # list of Instruction objects
        self.regstat = {}  # register/memory result status
        self.clock = 0
        self.count = 0

    # will update the scoreboard by one clock tick if possible
    # returns 0 if scoreboard can still run, returns 1 if it is finished
    def clock_tick(self):
        complete = True
        tick = False
        parse_num = -1
        issue_next = False

        # try to iterate any instructions
        for inst in self.insts:
            if inst.inst_num > self.count:
                break

            if inst.write == -1:
                if not tick:  # tick clock if it hasn't yet
                    self.clock += 1
                    tick = True

                complete = False
                # attempt to parse instruction that can be issued or has been
                parse_num = self.parse_instruction(inst)
                if parse_num == 1:
                    issue_next = True

        # check if all instructions have written back, ending the scoreboard
        for inst in self.insts:
            if inst.write == -1:
                complete = False
                break

        if complete:
            return 1
        else:
            # ready to issue next instruction
            if issue_next:
                self.count += 1
            self.free_regstat()
            self.free_read()
            self.free_fu()
            return 0

    # sends instruction to issue, read, execute, or write back stage
    def parse_instruction(self, instr):
        if instr.issue == -1:
            if self.issue(instr):
                return 1
        elif instr.read == -1:
            if self.read(instr):
                return 2
        elif instr.exec == -1:
            if self.execute(instr):
                return 3
        elif instr.write == -1:
            if self.write(instr):
                return 4

        return 0

    # checks for a functional unit and waw hazard before issuing instruction
    def issue(self, instr):
        inum = SUPPORTED[instr.inst[0]]
        inst_list = instr.inst
        waw_hazard = False
        dest = -1
        fj = None
        fk = None

        if inum == 2 or inum == 5:
            memory_location = inst_list[2].split('(')
            offset = int(memory_location[0])
            addr = int(memory_location[1].replace(')', ''))
            memory_location = offset + addr
            dest = memory_location

            if memory_location not in MEMORY:
                raise ValueError(memory_location, " is an invalid memory address")

            # check for waw hazard in memory location
            if memory_location in self.regstat:
                if self.regstat[memory_location] > 0:
                    waw_hazard = True

        else:
            reg_location = inst_list[1]
            dest = reg_location
            if reg_location not in REGISTERS:
                raise ValueError(reg_location, " is an invalid register")

            # check for waw hazard with register
            if reg_location in self.regstat:
                if self.regstat[reg_location][0] > 0:
                    waw_hazard = True

        funit = ""
        if inum > 0 and inum < 6:
            funit = "Int Unit"
        elif inum == 6 or inum == 7 or inum == 10:
            funit = "Int Unit"
        elif inum == 8 or inum == 9:
            funit = "FP Add"
        elif inum == 11:
            funit = "FP Mult"
        elif inum == 12:
            funit = "FP Div"

        # try to see if there is a functional unit available if no waw hazard
        if not waw_hazard:
            for unit in self.units:
                if unit.type_unit == funit and not unit.busy:
                    instr.issue = self.clock
                    unit.start_fu_execute(instr.inst_num)
                    unit.fi = dest
                    instr.funit = unit

                    # mark registers/memory we will write to and read from
                    self.regstat[dest] = (2, instr.inst_num)
                    self.read_from(instr)
                    return True

        return False

    # read from registers/memory if no raw hazard
    def read(self, instr):
        r1 = instr.funit.fj[0]
        r2 = instr.funit.fk[0]
        inst_list = instr.inst
        inum = SUPPORTED[inst_list[0]]
        raw_hazard = False

        # check if we need to wait for r1 or r2 to be written to first
        if r1 is not None:
            if r1 in self.regstat and self.regstat[r1][0] > 0:
                if self.regstat[r1][1] < instr.inst_num:
                    raw_hazard = True
        if r2 is not None:
            if r2 in self.regstat and self.regstat[r2][0] > 0:
                if self.regstat[r2][1] < instr.inst_num:
                    raw_hazard = True

        # we can then read from these registers if no raw hazards
        if not raw_hazard:
            # L.D and LW
            if inum == 1 or inum == 4:
                instr.funit.val1 = MEMORY[r1]
            # LI
            elif inum == 3:
                instr.funit.val1 = int(inst_list[2])
            # S.D and SW
            elif inum == 2 or inum == 5:
                instr.funit.val1 = REGISTERS[r1]
            # ADD and ADD.D
            elif inum == 6 or inum == 8:
                instr.funit.val1 = REGISTERS[r1]
                instr.funit.val2 = REGISTERS[r2]
            # ADDI
            elif inum == 7:
                instr.funit.val1 = REGISTERS[r1]
                instr.funit.val2 = int(inst_list[3])
            # SUB and SUB.D
            elif inum == 9 or inum == 10:
                instr.funit.val1 = REGISTERS[r1]
                instr.funit.val2 = REGISTERS[r2]
            # MUL.D
            elif inum == 11:
                instr.funit.val1 = REGISTERS[r1]
                instr.funit.val2 = REGISTERS[r2]
            # DIV.D
            elif inum == 12:
                instr.funit.val1 = REGISTERS[r1]
                instr.funit.val2 = REGISTERS[r2]

            instr.read = self.clock
            # clear up potential war hazard stall since read has occurred
            instr.funit.fj = (r1, 1)
            instr.funit. fk = (r2, 1)
            return True

        return False

    # execute instruction by incrementing time in functional unit
    def execute(self, instr):
        instr.funit.fu_execute()
        if instr.funit.time == instr.funit.exec_time:
            instr.exec = self.clock
        return True

    # write back to register/memory if no war hazard
    def write(self, instr):
        war_hazard = False
        # check if any previous instructions are trying to read from the
        # register/memory location we are trying to write to
        for unit in self.units:
            if unit.inst_num < instr.inst_num:
                fi = str(instr.funit.fi)
                if unit.fj[0] is not None:
                    if fi == str(unit.fj[0]) and unit.fj[1] > 0:
                        war_hazard = True
                if unit.fk[0] is not None:
                    if fi == str(unit.fk[0]) and unit.fk[1] > 0:
                        war_hazard = True

        if war_hazard:
            return False
        else:
            self.perform_instruction(instr)
            instr.write = self.clock
            self.regstat[instr.funit.fi] = (1, instr.inst_num)  # mark regstat to be freed
            instr.funit.inst_num = -1  # mark funit to be freed
            instr.funit = None
            return True

    # helper function for write to perform the instructions
    def perform_instruction(self, instr):
        inst_list = instr.inst
        inum = SUPPORTED[inst_list[0]]
        fi = instr.funit.fi  # will be a register/memory location
        fj = instr.funit.val1  # will be a value
        fk = instr.funit.val2  # will be a value

        # L.D and LW
        if inum == 1 or inum == 4:
            REGISTERS[fi] = fj
        # LI
        elif inum == 3:
            REGISTERS[fi] = fj
        # S.D and SW
        elif inum == 2 or inum == 5:
            MEMORY[fi] = fj
        # ADD
        elif inum == 6 or inum == 8:
            REGISTERS[fi] = fj + fk
        # ADD.D
        elif inum == 8:
            REGISTERS[fi] = float(fj + fk)
        # ADDI
        elif inum == 7:
            REGISTERS[fi] = fj + fk
        # SUB
        elif inum == 9:
            REGISTERS[fi] = fj - fk
        # SUB.D
        elif inum == 10:
            REGISTERS[fi] = float(fj - fk)
        # MUL.D
        elif inum == 11:
            REGISTERS[fi] = float(fj * fk)
        # DIV.D
        elif inum == 12:
            REGISTERS[fi] = float(fj / fk)

    # frees up registers/memory that has been written to
    def free_regstat(self):
        for stat in self.regstat:
            if self.regstat[stat][0] == 1:
                self.regstat[stat] = (0, self.regstat[stat][1])

    # frees up functional unit after instruction write back
    def free_fu(self):
        for unit in self.units:
            if unit.inst_num == -1:
                unit.modify_busy()

    # parse what registers/mem the instruction is trying to read from
    # so that we can prevent from war hazards
    def read_from(self, instr):
        inst_list = instr.inst
        inum = SUPPORTED[inst_list[0]]

        # L.D and LW
        if inum == 1 or inum == 4:
            memory_location = inst_list[2].split('(')
            offset = int(memory_location[0])
            addr = int(memory_location[1].replace(')', ''))
            instr.funit.fj = (offset + addr, 2)
            instr.funit.fk = (None, 2)
        # LI
        elif inum == 3:
            instr.funit.fj = (None, 2)
            instr.funit.fk = (None, 2)
        # S.D and SW
        elif inum == 2 or inum == 5:
            instr.funit.fj = (inst_list[1], 2)
            instr.funit.fk = (None, 2)
        # ADD and ADD.D
        elif inum == 6 or inum == 8:
            instr.funit.fj = (inst_list[2], 2)
            instr.funit.fk = (inst_list[3], 2)
        # ADDI
        elif inum == 7:
            instr.funit.fj = (inst_list[2], 2)
            instr.funit.fk = (None, 2)
        # SUB and SUB.D
        elif inum == 9 or inum == 10:
            instr.funit.fj = (inst_list[2], 2)
            instr.funit.fk = (inst_list[3], 2)
        # MUL.D
        elif inum == 11:
            instr.funit.fj = (inst_list[2], 2)
            instr.funit.fk = (inst_list[3], 2)
        # DIV.D
        elif inum == 12:
            instr.funit.fj = (inst_list[2], 2)
            instr.funit.fk = (inst_list[3], 2)

    # mark that we can write to a register, avoiding a war hazard
    def free_read(self):
        for unit in self.units:
            if unit.fj[1] == 1:
                unit.fj = (unit.fj[0], 0)
            if unit.fk[1] == 1:
                unit.fk = (unit.fk[0], 0)


# class Instruction: contains the instruction along with with when
# each of its stages were completed
class Instruction:

    def __init__(self, instruction, original, num):
        self.inst = instruction  # tokenized list for instruction
        self.string_rep = original  # original instruction string
        self.inst_num = num
        self.funit = None  # functional unit used for instruction
        self.issue = -1
        self.read = -1
        self.exec = -1
        self.write = -1


# class FunctionalUnit: can be one of four types of functional units. keeps track
# of destination and source of instructions along with source values
class FunctionalUnit:

    def __init__(self, type_u):
        self.type_unit = type_u
        self.exec_time = FU_CONFIG[type_u]
        self.time = 0
        self.busy = False
        self.inst_num = -1  # instruction ordering
        self.fi = -1  # dest
        self.fj = (-1, 0)  # (s1, read status)
        self.fk = (-1, 0)  # (s2, read status)
        self.val1 = -1  # value of s1
        self.val2 = -1  # value of s2

    # frees up functional unit
    def modify_busy(self):
        self.time = 0
        self.busy = False
        self.inst_num = -1
        self.fi = -1
        self.fj = (-1, 0)
        self.fk = (-1, 0)
        self.val1 = -1
        self.val2 = -1

    def fu_execute(self):
        self.time += 1

    def start_fu_execute(self, inst_number):
        self.busy = True
        self.inst_num = inst_number


if __name__ == '__main__':
    # make sure we get a valid file path for the number
    file_path = input("Please enter the file path of your program: ")
    while not os.path.exists(file_path):
        file_path = input("Please enter the file path of your program: ")

    program = TextParse(file_path)

    # get number of functional units for each type and add to scoreboard
    num_adders = int(input("How many FP adders? "))
    while num_adders < 1:
        num_adders = int(input("How many FP adders? "))

    num_mult = int(input("How many FP multipliers? "))
    while num_mult < 1:
        num_mult = int(input("How many FP multipliers? "))

    num_div = int(input("How many FP dividers? "))
    while num_div < 1:
        num_div = int(input("How many FP dividers? "))

    num_int = int(input("How many integer units? "))
    while num_int < 1:
        num_int = int(input("How many integer units? "))

    for x in range(num_adders):
        program.score_board.units.append(FunctionalUnit("FP Add"))

    for x in range(num_mult):
        program.score_board.units.append(FunctionalUnit("FP Mult"))

    for x in range(num_div):
        program.score_board.units.append(FunctionalUnit("FP Div"))

    for x in range(num_int):
        program.score_board.units.append(FunctionalUnit("Int Unit"))

    program.run()
