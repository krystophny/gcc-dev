TYPE TY0
    TYPE(TY0), ALLOCATABLE :: NODE0(:)
    TYPE(TY), ALLOCATABLE :: NODE4(:)
    TYPE(TY1),ALLOCATABLE :: NODE7(:)
    END TYPE
    TYPE TY1
        INTEGER,ALLOCATABLE :: II0
        TYPE(TY0) NODE2(4)
        TYPE(TY1), ALLOCATABLE :: NODE1(:)
        TYPE(TY),ALLOCATABLE :: NODE5(:)
        END TYPE
        TYPE TY
            INTEGER,ALLOCATABLE :: II(:)
            TYPE(TY1) NODE3(4)
            TYPE(TY),ALLOCATABLE :: NODE6(:)
            END TYPE
            TYPE BASE
                TYPE(TY),ALLOCATABLE :: OBJ(:)
                END TYPE
                TYPE(BASE)OBJ_BASE
                ALLOCATE(OBJ_BASE%OBJ(6))
                ALLOCATE(OBJ_BASE%OBJ(3))
                END
