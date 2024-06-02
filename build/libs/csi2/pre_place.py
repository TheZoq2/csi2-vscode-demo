ctx.createRectangularRegion("box1", 110, 40, 126, 55)
for cell, cellinfo in ctx.cells:
    # print(cell)
    if cell.startswith("dphy_frontend_0") or cell.startswith("clock_divider_0") or cell.startswith("lp_cleaner_0"):
        print("Floorplanned cell %s" % cell)
        ctx.constrainCellToRegion(cell, "box1")
