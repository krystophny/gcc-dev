      subroutine volatile_test ()
        implicit none
        integer(4), volatile :: va
        entry fun_a()
        return
        entry fun_b(va)
          call fun_c()
        return
      end
      subroutine fun_c ()
        implicit none
        call fun_a()
        return
      end
