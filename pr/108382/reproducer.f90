module yoethf
implicit none
real :: r2es, r3les, r3ies, r4les, r4ies, r5les, r5ies
real :: r5alvcp, r5alscp, ralvdcp, ralsdcp, ralfdcp, rtwat, rtice, rticecu
real :: rtwat_rtice_r, rtwat_rticecu_r, rkoop1, rkoop2
!$acc declare copyin(r2es, r3les, r3ies, r4les, r4ies, r5les, r5ies, &
!$acc   r5alvcp, r5alscp, ralvdcp, ralsdcp, ralfdcp, rtwat, rtice, rticecu, &
!$acc   rtwat_rtice_r, rtwat_rticecu_r, rkoop1, rkoop2)
!$omp declare target(r2es, r3les, r3ies, r4les, r4ies, r5les, r5ies , &
!$omp                r5alvcp, r5alscp, ralvdcp, ralsdcp, ralfdcp, rtwat, rtice, rticecu , &
!$omp                rtwat_rtice_r, rtwat_rticecu_r, rkoop1, rkoop2)
end module yoethf
