implicit none
integer :: arr(4)
integer :: i

do concurrent (i=1:5)
  associate (a=>i)
    forall( a=1:10,arr(a)==0)
    end forall
  end associate
end do
end
